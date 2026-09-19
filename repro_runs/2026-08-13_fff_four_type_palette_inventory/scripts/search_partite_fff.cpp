#include <algorithm>
#include <array>
#include <atomic>
#include <bit>
#include <cstdint>
#include <fstream>
#include <limits>
#include <mutex>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>

#include "partial_cycle.hpp"

using Perm = std::array<uint8_t, 10>;
using Table = std::array<Perm, 10>;
using Bits = std::vector<uint64_t>;

struct Graph {
  uint32_t n, words;
  Perm q1;
  std::vector<Perm> vertices;
  std::vector<Bits> adjacency;
};

static uint32_t read_u32(std::ifstream &input) {
  uint32_t value;
  input.read(reinterpret_cast<char *>(&value), sizeof(value));
  return value;
}

static Graph load_graph(const std::string &path) {
  std::ifstream input(path, std::ios::binary);
  char magic[8];
  input.read(magic, sizeof(magic));
  if (std::string(magic, 6) != "O8HTv1") throw std::runtime_error("bad graph");
  Graph graph;
  graph.n = read_u32(input);
  graph.words = read_u32(input);
  input.read(reinterpret_cast<char *>(graph.q1.data()), 10);
  graph.vertices.resize(graph.n);
  for (auto &vertex : graph.vertices) input.read(reinterpret_cast<char *>(vertex.data()), 10);
  graph.adjacency.assign(graph.n, Bits(graph.words));
  for (auto &row : graph.adjacency) {
    input.read(reinterpret_cast<char *>(row.data()), row.size() * sizeof(uint64_t));
  }
  if (!input) throw std::runtime_error("truncated graph");
  return graph;
}

static bool empty(const Bits &bits) {
  return std::all_of(bits.begin(), bits.end(), [](uint64_t word) { return word == 0; });
}
static uint64_t count(const Bits &bits) {
  uint64_t result = 0;
  for (uint64_t word : bits) result += std::popcount(word);
  return result;
}
static void clear(Bits &bits, uint32_t vertex) {
  bits[vertex / 64] &= ~(uint64_t{1} << (vertex % 64));
}
static uint32_t first(const Bits &bits) {
  for (uint32_t word = 0; word < bits.size(); ++word) {
    if (bits[word]) return word * 64 + std::countr_zero(bits[word]);
  }
  throw std::runtime_error("empty bitset");
}
static Bits intersect(const Bits &left, const Bits &right) {
  Bits result(left.size());
  for (size_t i = 0; i < left.size(); ++i) result[i] = left[i] & right[i];
  return result;
}

static bool creates_crossview_odd_cycle(const std::vector<Perm> &rows) {
  std::array<int8_t, 10> map{};
  for (int left = 0; left < 10; ++left) {
    for (int right = left + 1; right < 10; ++right) {
      map.fill(-1);
      for (const Perm &row : rows) map[row[left]] = row[right];
      if (order8::partial_map_has_odd_cycle(map)) return true;
    }
  }

  for (int left_symbol = 0; left_symbol < 10; ++left_symbol) {
    for (int right_symbol = left_symbol + 1; right_symbol < 10; ++right_symbol) {
      map.fill(-1);
      for (const Perm &row : rows) {
        int left_col = -1, right_col = -1;
        for (int col = 0; col < 10; ++col) {
          if (row[col] == left_symbol) left_col = col;
          if (row[col] == right_symbol) right_col = col;
        }
        map[left_col] = right_col;
      }
      if (order8::partial_map_has_odd_cycle(map)) return true;
    }
  }
  return false;
}

struct Search {
  const Graph &graph;
  const std::array<Bits, 8> &buckets;
  std::atomic<uint64_t> &nodes;
  std::atomic<uint64_t> &crossview_prunes;
  std::atomic<bool> &found;
  std::mutex &witness_mutex;
  Table &witness;

  void dfs(uint8_t unused, std::vector<uint32_t> &chosen, std::vector<Perm> &rows,
           const Bits &candidates) {
    if (found.load(std::memory_order_relaxed)) return;
    nodes.fetch_add(1, std::memory_order_relaxed);
    if (creates_crossview_odd_cycle(rows)) {
      crossview_prunes.fetch_add(1, std::memory_order_relaxed);
      return;
    }
    if (!unused) {
      std::lock_guard<std::mutex> lock(witness_mutex);
      if (!found.exchange(true)) {
        for (int i = 0; i < 10; ++i) witness[i] = rows[i];
      }
      return;
    }

    int selected_bucket = -1;
    uint64_t smallest = std::numeric_limits<uint64_t>::max();
    Bits selected;
    for (int bucket = 0; bucket < 8; ++bucket) {
      if (!(unused & (1u << bucket))) continue;
      Bits current = intersect(candidates, buckets[bucket]);
      uint64_t size = count(current);
      if (!size) return;
      if (size < smallest) {
        smallest = size;
        selected_bucket = bucket;
        selected = std::move(current);
      }
    }
    while (!empty(selected) && !found.load(std::memory_order_relaxed)) {
      uint32_t vertex = first(selected);
      clear(selected, vertex);
      chosen.push_back(vertex);
      rows.push_back(graph.vertices[vertex]);
      dfs(unused & ~(1u << selected_bucket), chosen, rows,
          intersect(candidates, graph.adjacency[vertex]));
      rows.pop_back();
      chosen.pop_back();
    }
  }
};

static void write_table(std::ostream &output, const Table &table) {
  output << "{\n  \"table\": [";
  for (int row = 0; row < 10; ++row) {
    if (row) output << ',';
    output << '[';
    for (int col = 0; col < 10; ++col) {
      if (col) output << ',';
      output << static_cast<int>(table[row][col]);
    }
    output << ']';
  }
  output << "]\n}\n";
}

int main(int argc, char **argv) {
  if (argc != 10) {
    throw std::runtime_error(
        "usage: search GRAPH WORKERS TASK_START TASK_COUNT RESULT SUMMARY TABLE LABEL MODE");
  }
  Graph graph = load_graph(argv[1]);
  int workers = std::stoi(argv[2]);
  uint32_t requested_start = std::stoul(argv[3]);
  uint32_t requested_count = std::stoul(argv[4]);
  std::array<Bits, 8> buckets;
  for (auto &bucket : buckets) bucket.assign(graph.words, 0);
  for (uint32_t vertex = 0; vertex < graph.n; ++vertex) {
    int bucket = graph.vertices[vertex][0] - 2;
    buckets[bucket][vertex / 64] |= uint64_t{1} << (vertex % 64);
  }
  int initial_bucket = 0;
  for (int bucket = 1; bucket < 8; ++bucket) {
    if (count(buckets[bucket]) < count(buckets[initial_bucket])) initial_bucket = bucket;
  }
  Bits root = buckets[initial_bucket];
  std::vector<uint32_t> tasks;
  while (!empty(root)) {
    uint32_t vertex = first(root);
    clear(root, vertex);
    tasks.push_back(vertex);
  }
  uint32_t start = std::min<uint32_t>(requested_start, tasks.size());
  uint32_t end = requested_count == 0
      ? tasks.size()
      : std::min<uint32_t>(tasks.size(), start + requested_count);

  std::atomic<uint32_t> next{start};
  std::atomic<uint32_t> completed{0};
  std::atomic<uint64_t> nodes{0}, prunes{0};
  std::atomic<bool> found{false};
  std::mutex witness_mutex;
  Table witness{};
  auto worker = [&]() {
    Search search{graph, buckets, nodes, prunes, found, witness_mutex, witness};
    while (!found.load()) {
      uint32_t task_index = next.fetch_add(1);
      if (task_index >= end) return;
      std::vector<uint32_t> chosen{tasks[task_index]};
      std::vector<Perm> rows{Perm{0,1,2,3,4,5,6,7,8,9}, graph.q1,
                             graph.vertices[tasks[task_index]]};
      search.dfs(uint8_t(0xff & ~(1u << initial_bucket)), chosen, rows,
                 graph.adjacency[tasks[task_index]]);
      completed.fetch_add(1);
    }
  };
  std::vector<std::thread> pool;
  for (int i = 0; i < workers; ++i) pool.emplace_back(worker);
  for (auto &thread : pool) thread.join();

  bool complete = !found.load() && completed.load() == end - start;
  std::ofstream result(argv[5]);
  result << "{\n  \"label\": \"" << argv[8] << "\",\n"
         << "  \"mode\": \"" << argv[9] << "\",\n"
         << "  \"workers\": " << workers << ",\n"
         << "  \"total_initial_tasks\": " << tasks.size() << ",\n"
         << "  \"task_start\": " << start << ",\n"
         << "  \"task_end_exclusive\": " << end << ",\n"
         << "  \"completed_tasks\": " << completed.load() << ",\n"
         << "  \"search_nodes\": " << nodes.load() << ",\n"
         << "  \"crossview_odd_cycle_prunes\": " << prunes.load() << ",\n"
         << "  \"fff_found\": " << (found.load() ? "true" : "false") << ",\n"
         << "  \"slice_complete\": " << (complete ? "true" : "false") << "\n}\n";
  std::ofstream summary(argv[6]);
  summary << "Cross-view-pruned partite FFF search\n\n"
          << "label/mode: " << argv[8] << '/' << argv[9] << '\n'
          << "total tasks: " << tasks.size() << '\n'
          << "slice: [" << start << ',' << end << ")\n"
          << "completed tasks: " << completed.load() << '\n'
          << "search nodes: " << nodes.load() << '\n'
          << "cross-view odd-cycle prunes: " << prunes.load() << '\n'
          << "FFF found: " << (found.load() ? "true" : "false") << '\n'
          << "slice complete: " << (complete ? "true" : "false") << '\n';
  if (found.load()) {
    std::ofstream table(argv[7]);
    write_table(table, witness);
  }
}
