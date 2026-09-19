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
  const std::array<char, 8> expected_magic{'O','8','H','T','v','1','\0','\0'};
  std::array<char, 8> magic{};
  input.read(magic.data(), magic.size());
  if (magic != expected_magic) throw std::runtime_error("bad graph magic");
  Graph graph;
  graph.n = read_u32(input);
  graph.words = read_u32(input);
  if (graph.words != (graph.n + 63) / 64) {
    throw std::runtime_error("bad graph word count");
  }
  input.read(reinterpret_cast<char *>(graph.q1.data()), 10);
  graph.vertices.resize(graph.n);
  for (auto &vertex : graph.vertices) input.read(reinterpret_cast<char *>(vertex.data()), 10);
  graph.adjacency.assign(graph.n, Bits(graph.words));
  for (auto &row : graph.adjacency) {
    input.read(reinterpret_cast<char *>(row.data()), row.size() * sizeof(uint64_t));
  }
  if (!input || input.peek() != std::ifstream::traits_type::eof()) {
    throw std::runtime_error("truncated graph or trailing bytes");
  }
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

struct PartialChannels {
  using Map = std::array<int8_t, 10>;
  std::array<Map, 45> column{};
  std::array<Map, 45> symbol{};

  PartialChannels() {
    for (Map &map : column) map.fill(-1);
    for (Map &map : symbol) map.fill(-1);
  }

  static bool add_edge(Map &map, int source, int target) {
    if (map[source] != -1) throw std::runtime_error("partial-map source collision");
    map[source] = target;
    int length = 1;
    int current = target;
    while (current != source && map[current] != -1) {
      current = map[current];
      ++length;
      if (length > 10) throw std::runtime_error("malformed partial permutation");
    }
    return current == source && length % 2 == 1;
  }

  bool push(const Perm &row) {
    Perm inverse_row{};
    for (int col = 0; col < 10; ++col) inverse_row[row[col]] = col;
    bool odd = false;
    int channel = 0;
    for (int left = 0; left < 10; ++left) {
      for (int right = left + 1; right < 10; ++right) {
        odd |= add_edge(column[channel], row[left], row[right]);
        odd |= add_edge(symbol[channel], inverse_row[left], inverse_row[right]);
        ++channel;
      }
    }
    return !odd;
  }

  void pop(const Perm &row) {
    Perm inverse_row{};
    for (int col = 0; col < 10; ++col) inverse_row[row[col]] = col;
    int channel = 0;
    for (int left = 0; left < 10; ++left) {
      for (int right = left + 1; right < 10; ++right) {
        column[channel][row[left]] = -1;
        symbol[channel][inverse_row[left]] = -1;
        ++channel;
      }
    }
  }
};

struct Search {
  const Graph &graph;
  const std::array<Bits, 8> &buckets;
  PartialChannels &channels;
  std::atomic<uint64_t> &nodes;
  std::atomic<uint64_t> &crossview_prunes;
  std::atomic<bool> &found;
  std::mutex &witness_mutex;
  Table &witness;
  std::array<uint32_t, 8> word_begin{};
  std::array<std::array<Bits, 8>, 8> scratch;

  Search(const Graph &graph_value, const std::array<Bits, 8> &bucket_values,
         PartialChannels &channel_value, std::atomic<uint64_t> &node_value,
         std::atomic<uint64_t> &prune_value, std::atomic<bool> &found_value,
         std::mutex &mutex_value, Table &witness_value)
      : graph(graph_value), buckets(bucket_values), channels(channel_value),
        nodes(node_value), crossview_prunes(prune_value), found(found_value),
        witness_mutex(mutex_value), witness(witness_value) {
    for (int bucket = 0; bucket < 8; ++bucket) {
      uint32_t begin = 0;
      while (begin < graph.words && !buckets[bucket][begin]) ++begin;
      if (begin == graph.words) throw std::runtime_error("empty image bucket");
      uint32_t end = graph.words;
      while (end > begin && !buckets[bucket][end - 1]) --end;
      word_begin[bucket] = begin;
      for (int depth = 0; depth < 8; ++depth) {
        scratch[depth][bucket].resize(end - begin);
      }
    }
  }

  void initialize(uint32_t root_vertex, int initial_bucket) {
    for (int bucket = 0; bucket < 8; ++bucket) {
      if (bucket == initial_bucket) continue;
      Bits &initial = scratch[0][bucket];
      uint32_t begin = word_begin[bucket];
      for (uint32_t word = 0; word < initial.size(); ++word) {
        initial[word] = graph.adjacency[root_vertex][begin + word]
            & buckets[bucket][begin + word];
      }
    }
  }

  void dfs(uint8_t unused, int depth, std::vector<Perm> &rows,
           bool crossview_valid) {
    if (found.load(std::memory_order_relaxed)) return;
    nodes.fetch_add(1, std::memory_order_relaxed);
    if (!crossview_valid) {
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
    for (int bucket = 0; bucket < 8; ++bucket) {
      if (!(unused & (1u << bucket))) continue;
      uint64_t size = count(scratch[depth][bucket]);
      if (!size) return;
      if (size < smallest) {
        smallest = size;
        selected_bucket = bucket;
      }
    }
    const Bits &selected = scratch[depth][selected_bucket];
    for (uint32_t local_word = 0; local_word < selected.size(); ++local_word) {
      uint64_t bits = selected[local_word];
      while (bits && !found.load(std::memory_order_relaxed)) {
        uint32_t vertex = (word_begin[selected_bucket] + local_word) * 64
            + std::countr_zero(bits);
        bits &= bits - 1;
        rows.push_back(graph.vertices[vertex]);
        bool valid = channels.push(graph.vertices[vertex]);
        uint8_t next_unused = unused & ~(1u << selected_bucket);
        if (valid) {
          for (int bucket = 0; bucket < 8; ++bucket) {
            if (!(next_unused & (1u << bucket))) continue;
            const Bits &current = scratch[depth][bucket];
            Bits &next = scratch[depth + 1][bucket];
            uint32_t begin = word_begin[bucket];
            for (uint32_t word = 0; word < current.size(); ++word) {
              next[word] = current[word] & graph.adjacency[vertex][begin + word];
            }
          }
        }
        dfs(next_unused, depth + 1, rows, valid);
        channels.pop(graph.vertices[vertex]);
        rows.pop_back();
      }
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
  if (argc != 10 && argc != 11) {
    throw std::runtime_error(
        "usage: search GRAPH WORKERS TASK_START TASK_COUNT RESULT SUMMARY TABLE LABEL MODE [TASK_ORDINALS]");
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
  uint32_t full_initial_tasks = tasks.size();
  if (argc == 11) {
    std::ifstream task_input(argv[10]);
    std::vector<uint32_t> selected;
    uint32_t ordinal;
    while (task_input >> ordinal) {
      if (ordinal >= tasks.size()) throw std::runtime_error("task ordinal out of range");
      if (!selected.empty() && ordinal <= selected.back()) {
        throw std::runtime_error("task ordinals not strictly increasing");
      }
      selected.push_back(tasks[ordinal]);
    }
    if (!task_input.eof() || selected.empty()) {
      throw std::runtime_error("invalid or empty task ordinal file");
    }
    tasks = std::move(selected);
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
    PartialChannels channels;
    const Perm identity{0,1,2,3,4,5,6,7,8,9};
    if (!channels.push(identity) || !channels.push(graph.q1)) {
      throw std::runtime_error("canonical first rows already violate cross-view F");
    }
    Search search(graph, buckets, channels, nodes, prunes, found, witness_mutex, witness);
    while (!found.load()) {
      uint32_t task_index = next.fetch_add(1);
      if (task_index >= end) return;
      std::vector<Perm> rows{identity, graph.q1,
                             graph.vertices[tasks[task_index]]};
      bool valid = channels.push(graph.vertices[tasks[task_index]]);
      search.initialize(tasks[task_index], initial_bucket);
      search.dfs(uint8_t(0xff & ~(1u << initial_bucket)), 0, rows, valid);
      channels.pop(graph.vertices[tasks[task_index]]);
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
         << "  \"full_initial_tasks\": " << full_initial_tasks << ",\n"
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
          << "full initial tasks: " << full_initial_tasks << '\n'
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
