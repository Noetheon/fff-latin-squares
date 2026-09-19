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

using Perm = std::array<uint8_t, 10>;
using Table = std::array<Perm, 10>;
using Type = std::vector<int>;

struct Graph {
  uint32_t n = 0;
  uint32_t words = 0;
  Perm root{};
  std::vector<Perm> vertices;
  std::vector<std::vector<uint64_t>> adjacency;
};

struct Totals {
  uint64_t cliques = 0;
  uint64_t latin_errors = 0;
  uint64_t row_not_f_errors = 0;
  uint64_t palette_subset_errors = 0;
  uint64_t exact_palette = 0;
  uint64_t fff = 0;
  std::array<uint64_t, 8> patterns{};
};

static uint32_t read_u32(std::ifstream &input) {
  uint32_t value;
  input.read(reinterpret_cast<char *>(&value), sizeof(value));
  return value;
}

static Graph load_graph(const std::string &path) {
  std::ifstream input(path, std::ios::binary);
  std::array<char, 8> magic{};
  input.read(magic.data(), magic.size());
  const std::array<char, 8> expected{'O','8','H','T','v','1','\0','\0'};
  if (magic != expected) throw std::runtime_error("bad graph magic");
  Graph graph;
  graph.n = read_u32(input);
  graph.words = read_u32(input);
  if (graph.words != (graph.n + 63) / 64) throw std::runtime_error("bad word count");
  input.read(reinterpret_cast<char *>(graph.root.data()), graph.root.size());
  graph.vertices.resize(graph.n);
  for (auto &vertex : graph.vertices) {
    input.read(reinterpret_cast<char *>(vertex.data()), vertex.size());
  }
  graph.adjacency.assign(graph.n, std::vector<uint64_t>(graph.words));
  for (auto &row : graph.adjacency) {
    input.read(reinterpret_cast<char *>(row.data()), row.size() * sizeof(uint64_t));
  }
  if (!input || input.peek() != std::ifstream::traits_type::eof()) {
    throw std::runtime_error("truncated graph or trailing bytes");
  }
  return graph;
}

static Type parse_type(std::string text) {
  Type type;
  size_t start = 0;
  while (true) {
    size_t end = text.find('+', start);
    type.push_back(std::stoi(text.substr(start, end - start)));
    if (end == std::string::npos) break;
    start = end + 1;
  }
  std::sort(type.rbegin(), type.rend());
  return type;
}

static uint64_t type_code(const Type &type) {
  uint64_t code = 0;
  for (int length : type) code += uint64_t{1} << (4 * length);
  return code;
}

static Type cycle_type(const Perm &permutation) {
  std::array<bool, 10> seen{};
  Type type;
  for (int start = 0; start < 10; ++start) {
    if (seen[start]) continue;
    int current = start;
    int length = 0;
    do {
      seen[current] = true;
      current = permutation[current];
      ++length;
    } while (current != start);
    type.push_back(length);
  }
  std::sort(type.rbegin(), type.rend());
  return type;
}

static bool is_f(const Perm &permutation) {
  Type type = cycle_type(permutation);
  return std::all_of(type.begin(), type.end(), [](int length) {
    return length % 2 == 0;
  });
}

static Perm inverse(const Perm &permutation) {
  Perm result{};
  for (int point = 0; point < 10; ++point) result[permutation[point]] = point;
  return result;
}

static Perm relative(const Perm &left, const Perm &right) {
  Perm inverse_left = inverse(left);
  Perm result{};
  for (int point = 0; point < 10; ++point) result[point] = right[inverse_left[point]];
  return result;
}

static bool latin(const Table &table) {
  for (const Perm &row : table) {
    std::array<int, 10> counts{};
    for (int value : row) {
      if (value < 0 || value >= 10) return false;
      ++counts[value];
    }
    if (std::any_of(counts.begin(), counts.end(), [](int count) { return count != 1; })) {
      return false;
    }
  }
  for (int col = 0; col < 10; ++col) {
    std::array<int, 10> counts{};
    for (const Perm &row : table) ++counts[row[col]];
    if (std::any_of(counts.begin(), counts.end(), [](int count) { return count != 1; })) {
      return false;
    }
  }
  return true;
}

static uint8_t pattern(const Table &table) {
  bool row_f = true;
  bool col_f = true;
  bool sym_f = true;
  for (int left = 0; left < 10; ++left) {
    for (int right = left + 1; right < 10; ++right) {
      row_f &= is_f(relative(table[left], table[right]));
      Perm col{};
      for (const Perm &row : table) col[row[left]] = row[right];
      col_f &= is_f(col);
      Perm sym{};
      for (const Perm &row : table) {
        int left_col = -1;
        int right_col = -1;
        for (int column = 0; column < 10; ++column) {
          if (row[column] == left) left_col = column;
          if (row[column] == right) right_col = column;
        }
        sym[left_col] = right_col;
      }
      sym_f &= is_f(sym);
    }
  }
  return (row_f ? 4 : 0) | (col_f ? 2 : 0) | (sym_f ? 1 : 0);
}

static bool adjacent(const Graph &graph, uint32_t left, uint32_t right) {
  return graph.adjacency[left][right / 64] & (uint64_t{1} << (right % 64));
}

static uint64_t bit_count(const std::vector<uint64_t> &bits) {
  uint64_t result = 0;
  for (uint64_t word : bits) result += std::popcount(word);
  return result;
}

static std::vector<uint64_t> intersect(
    const std::vector<uint64_t> &left, const std::vector<uint64_t> &right) {
  std::vector<uint64_t> result(left.size());
  for (size_t index = 0; index < left.size(); ++index) result[index] = left[index] & right[index];
  return result;
}

static uint32_t first_vertex(const std::vector<uint64_t> &bits) {
  for (uint32_t word = 0; word < bits.size(); ++word) {
    if (bits[word]) return word * 64 + std::countr_zero(bits[word]);
  }
  throw std::runtime_error("empty bitset");
}

static void clear_vertex(std::vector<uint64_t> &bits, uint32_t vertex) {
  bits[vertex / 64] &= ~(uint64_t{1} << (vertex % 64));
}

struct Enumerator {
  const Graph &graph;
  const std::array<std::vector<uint32_t>, 8> &buckets;
  const std::array<std::vector<uint64_t>, 8> &bucket_bits;
  const std::vector<uint64_t> &palette;
  Totals totals;
  std::array<uint32_t, 8> chosen{};

  void complete() {
    ++totals.cliques;
    Table table{};
    for (int value = 0; value < 10; ++value) table[0][value] = value;
    table[1] = graph.root;
    for (int index = 0; index < 8; ++index) table[index + 2] = graph.vertices[chosen[index]];
    if (!latin(table)) {
      ++totals.latin_errors;
      return;
    }
    std::vector<uint64_t> used;
    bool row_f = true;
    for (int left = 0; left < 10; ++left) {
      for (int right = left + 1; right < 10; ++right) {
        Perm rel = relative(table[left], table[right]);
        row_f &= is_f(rel);
        used.push_back(type_code(cycle_type(rel)));
      }
    }
    std::sort(used.begin(), used.end());
    used.erase(std::unique(used.begin(), used.end()), used.end());
    if (!std::includes(palette.begin(), palette.end(), used.begin(), used.end())) {
      ++totals.palette_subset_errors;
    }
    if (used == palette) ++totals.exact_palette;
    if (!row_f) ++totals.row_not_f_errors;
    uint8_t value = pattern(table);
    ++totals.patterns[value];
    if (value == 7) ++totals.fff;
  }

  void dfs(uint8_t unused, const std::vector<uint64_t> &candidates) {
    if (!unused) {
      complete();
      return;
    }

    int selected_bucket = -1;
    uint64_t smallest = std::numeric_limits<uint64_t>::max();
    std::vector<uint64_t> selected;
    for (int bucket = 0; bucket < 8; ++bucket) {
      if (!(unused & (1u << bucket))) continue;
      std::vector<uint64_t> current = intersect(candidates, bucket_bits[bucket]);
      uint64_t size = bit_count(current);
      if (!size) return;
      if (size < smallest) {
        smallest = size;
        selected_bucket = bucket;
        selected = std::move(current);
      }
    }
    while (bit_count(selected)) {
      uint32_t vertex = first_vertex(selected);
      clear_vertex(selected, vertex);
      chosen[selected_bucket] = vertex;
      dfs(unused & ~(1u << selected_bucket), intersect(candidates, graph.adjacency[vertex]));
    }
  }
};

static std::string pattern_name(int value) {
  std::string result;
  result += value & 4 ? 'F' : 'T';
  result += value & 2 ? 'F' : 'T';
  result += value & 1 ? 'F' : 'T';
  return result;
}

int main(int argc, char **argv) {
  if (argc != 10) {
    throw std::runtime_error(
        "usage: enumerate GRAPH TYPE1 TYPE2 TYPE3 TYPE4 TYPE5 WORKERS OUTPUT SUMMARY");
  }
  Graph graph = load_graph(argv[1]);
  std::vector<uint64_t> palette;
  for (int index = 2; index < 7; ++index) palette.push_back(type_code(parse_type(argv[index])));
  std::sort(palette.begin(), palette.end());
  palette.erase(std::unique(palette.begin(), palette.end()), palette.end());
  if (palette.size() != 5) throw std::runtime_error("palette is not five distinct types");
  int workers = std::max(1, std::stoi(argv[7]));
  std::array<std::vector<uint32_t>, 8> buckets;
  for (uint32_t vertex = 0; vertex < graph.n; ++vertex) {
    int bucket = graph.vertices[vertex][0] - 2;
    if (bucket < 0 || bucket >= 8) throw std::runtime_error("invalid bucket");
    buckets[bucket].push_back(vertex);
  }
  std::array<std::vector<uint64_t>, 8> bucket_bits;
  for (int bucket = 0; bucket < 8; ++bucket) {
    bucket_bits[bucket].assign(graph.words, 0);
    for (uint32_t vertex : buckets[bucket]) {
      bucket_bits[bucket][vertex / 64] |= uint64_t{1} << (vertex % 64);
    }
  }

  std::atomic<uint32_t> next{0};
  std::mutex mutex;
  Totals total;
  auto worker = [&]() {
    Totals local;
    while (true) {
      uint32_t task = next.fetch_add(1);
      if (task >= buckets[0].size()) break;
      Enumerator enumerator{graph, buckets, bucket_bits, palette};
      enumerator.chosen[0] = buckets[0][task];
      enumerator.dfs(0xfe, graph.adjacency[buckets[0][task]]);
      local.cliques += enumerator.totals.cliques;
      local.latin_errors += enumerator.totals.latin_errors;
      local.row_not_f_errors += enumerator.totals.row_not_f_errors;
      local.palette_subset_errors += enumerator.totals.palette_subset_errors;
      local.exact_palette += enumerator.totals.exact_palette;
      local.fff += enumerator.totals.fff;
      for (int i = 0; i < 8; ++i) local.patterns[i] += enumerator.totals.patterns[i];
    }
    std::lock_guard<std::mutex> lock(mutex);
    total.cliques += local.cliques;
    total.latin_errors += local.latin_errors;
    total.row_not_f_errors += local.row_not_f_errors;
    total.palette_subset_errors += local.palette_subset_errors;
    total.exact_palette += local.exact_palette;
    total.fff += local.fff;
    for (int i = 0; i < 8; ++i) total.patterns[i] += local.patterns[i];
  };
  std::vector<std::thread> pool;
  for (int index = 0; index < workers; ++index) pool.emplace_back(worker);
  for (auto &thread : pool) thread.join();

  bool valid = total.latin_errors == 0 && total.row_not_f_errors == 0
      && total.palette_subset_errors == 0;
  std::ofstream output(argv[8]);
  output << "{\n  \"schema_version\": \"independent-binary-graph-clique-table-audit-v1\",\n"
         << "  \"workers\": " << workers << ",\n"
         << "  \"initial_tasks\": " << buckets[0].size() << ",\n"
         << "  \"clique_count\": " << total.cliques << ",\n"
         << "  \"exact_palette_count\": " << total.exact_palette << ",\n"
         << "  \"fff_count\": " << total.fff << ",\n"
         << "  \"latin_errors\": " << total.latin_errors << ",\n"
         << "  \"row_not_f_errors\": " << total.row_not_f_errors << ",\n"
         << "  \"palette_subset_errors\": " << total.palette_subset_errors << ",\n"
         << "  \"pattern_counts\": {";
  bool first = true;
  for (int value = 0; value < 8; ++value) {
    if (!total.patterns[value]) continue;
    if (!first) output << ',';
    first = false;
    output << "\n    \"" << pattern_name(value) << "\": " << total.patterns[value];
  }
  if (!first) output << '\n';
  output << "  },\n  \"valid\": " << (valid ? "true" : "false") << "\n}\n";

  std::ofstream summary(argv[9]);
  summary << "Independent binary-graph clique-table audit\n\n"
          << "workers/tasks: " << workers << '/' << buckets[0].size() << '\n'
          << "8-cliques: " << total.cliques << '\n'
          << "exact palette tables: " << total.exact_palette << '\n'
          << "FFF tables: " << total.fff << '\n'
          << "Latin/row-F/palette-subset errors: " << total.latin_errors << '/'
          << total.row_not_f_errors << '/' << total.palette_subset_errors << '\n';
  for (int value = 0; value < 8; ++value) {
    if (total.patterns[value]) summary << pattern_name(value) << ": " << total.patterns[value] << '\n';
  }
  summary << "valid: " << (valid ? "true" : "false") << '\n';
  return valid ? 0 : 1;
}
