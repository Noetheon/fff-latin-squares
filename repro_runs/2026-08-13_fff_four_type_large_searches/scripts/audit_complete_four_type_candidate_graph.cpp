#include <algorithm>
#include <array>
#include <atomic>
#include <cstdint>
#include <fstream>
#include <numeric>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>

#include "partial_cycle.hpp"

using Perm = std::array<uint8_t, 10>;
using Type = std::vector<int>;

static uint32_t read_u32(std::ifstream &input) {
  uint32_t value;
  input.read(reinterpret_cast<char *>(&value), sizeof(value));
  return value;
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

static Type cycle_type(const Perm &permutation) {
  std::array<bool, 10> seen{};
  Type type;
  for (int point = 0; point < 10; ++point) {
    if (seen[point]) continue;
    int length = 0;
    int current = point;
    do {
      seen[current] = true;
      current = permutation[current];
      ++length;
    } while (current != point);
    type.push_back(length);
  }
  std::sort(type.rbegin(), type.rend());
  return type;
}

static uint64_t cycle_code(const Perm &permutation) {
  std::array<bool, 10> seen{};
  uint64_t code = 0;
  for (int point = 0; point < 10; ++point) {
    if (seen[point]) continue;
    int length = 0;
    int current = point;
    do {
      seen[current] = true;
      current = permutation[current];
      ++length;
    } while (current != point);
    code += uint64_t{1} << (4 * length);
  }
  return code;
}

static uint64_t type_code(const Type &type) {
  uint64_t code = 0;
  for (int length : type) code += uint64_t{1} << (4 * length);
  return code;
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

static Perm relative_from_inverse(const Perm &inverse_left, const Perm &right) {
  Perm result{};
  for (int point = 0; point < 10; ++point) result[point] = right[inverse_left[point]];
  return result;
}

static bool allowed(const Type &type, const std::array<Type, 4> &palette) {
  return std::find(palette.begin(), palette.end(), type) != palette.end();
}

static bool allowed_code(uint64_t code, const std::array<uint64_t, 4> &palette) {
  return std::find(palette.begin(), palette.end(), code) != palette.end();
}

template <size_t RowCount>
static bool creates_crossview_odd_cycle(const std::array<Perm, RowCount> &rows) {
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
        int left_col = -1;
        int right_col = -1;
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

int main(int argc, char **argv) {
  if (argc != 10 && argc != 11) return 2;
  std::array<Type, 4> palette{parse_type(argv[1]), parse_type(argv[2]),
      parse_type(argv[3]), parse_type(argv[4])};
  std::array<uint64_t, 4> palette_codes{type_code(palette[0]),
      type_code(palette[1]), type_code(palette[2]), type_code(palette[3])};
  Type root_type = parse_type(argv[5]);
  int filter_level = std::stoi(argv[6]);
  int workers = argc == 11 ? std::max(1, std::stoi(argv[10])) : 1;

  std::ifstream input(argv[7], std::ios::binary);
  const std::array<char, 8> expected_magic{'O','8','H','T','v','1','\0','\0'};
  std::array<char, 8> magic{};
  input.read(magic.data(), magic.size());
  uint32_t count = read_u32(input);
  uint32_t words = read_u32(input);
  Perm root{};
  input.read(reinterpret_cast<char *>(root.data()), root.size());
  std::vector<Perm> vertices(count);
  for (auto &vertex : vertices) {
    input.read(reinterpret_cast<char *>(vertex.data()), vertex.size());
  }
  std::vector<std::vector<uint64_t>> adjacency(
      count, std::vector<uint64_t>(words));
  for (auto &row : adjacency) {
    input.read(reinterpret_cast<char *>(row.data()), row.size() * sizeof(uint64_t));
  }
  uint64_t format_errors = magic != expected_magic;
  format_errors += words != (count + 63) / 64;
  format_errors += !input;
  format_errors += input && input.peek() != std::ifstream::traits_type::eof();
  uint64_t diagonal_errors = 0;
  uint64_t padding_errors = 0;
  if (words == (count + 63) / 64) {
    uint64_t final_mask = count % 64
        ? (uint64_t{1} << (count % 64)) - 1
        : ~uint64_t{0};
    for (uint32_t row = 0; row < count; ++row) {
      diagonal_errors += (adjacency[row][row / 64] >> (row % 64)) & 1u;
      padding_errors += (adjacency[row].back() & ~final_mask) != 0;
    }
  }
  std::vector<Perm> inverse_vertices(count);
  for (uint32_t index = 0; index < count; ++index) {
    inverse_vertices[index] = inverse(vertices[index]);
  }

  Perm identity{};
  std::iota(identity.begin(), identity.end(), 0);
  Perm candidate = identity;
  std::vector<Perm> expected_vertices;
  do {
    if (!allowed_code(cycle_code(candidate), palette_codes) ||
        !allowed_code(cycle_code(relative(root, candidate)), palette_codes)) {
      continue;
    }
    if (filter_level >= 1 && creates_crossview_odd_cycle(
            std::array<Perm, 3>{identity, root, candidate})) continue;
    expected_vertices.push_back(candidate);
  } while (std::next_permutation(candidate.begin(), candidate.end()));

  uint64_t list_errors = expected_vertices.size() != vertices.size();
  size_t common = std::min(expected_vertices.size(), vertices.size());
  for (size_t index = 0; index < common; ++index) {
    if (expected_vertices[index] != vertices[index]) ++list_errors;
  }

  std::atomic<uint32_t> next_left{0};
  std::vector<uint64_t> local_pairs(workers);
  std::vector<uint64_t> local_edges(workers);
  std::vector<uint64_t> local_errors(workers);
  std::vector<uint64_t> local_reverse_errors(workers);
  auto audit_rows = [&](int worker) {
    while (true) {
      uint32_t left = next_left.fetch_add(1);
      if (left >= count) break;
      for (uint32_t right = left + 1; right < count; ++right) {
        bool expected = allowed_code(cycle_code(relative_from_inverse(
            inverse_vertices[left], vertices[right])), palette_codes);
        if (expected && filter_level >= 2 && creates_crossview_odd_cycle(
                std::array<Perm, 4>{identity, root, vertices[left], vertices[right]})) {
          expected = false;
        }
        bool stored = adjacency[left][right / 64] & (uint64_t{1} << (right % 64));
        bool reverse_stored = adjacency[right][left / 64] & (uint64_t{1} << (left % 64));
        ++local_pairs[worker];
        local_edges[worker] += stored;
        local_errors[worker] += expected != stored;
        local_reverse_errors[worker] += stored != reverse_stored;
      }
    }
  };
  std::vector<std::thread> pool;
  for (int worker = 0; worker < workers; ++worker) pool.emplace_back(audit_rows, worker);
  for (auto &thread : pool) thread.join();
  uint64_t pairs = std::accumulate(local_pairs.begin(), local_pairs.end(), uint64_t{0});
  uint64_t edges = std::accumulate(local_edges.begin(), local_edges.end(), uint64_t{0});
  uint64_t edge_errors = std::accumulate(local_errors.begin(), local_errors.end(), uint64_t{0});
  uint64_t reverse_edge_errors = std::accumulate(
      local_reverse_errors.begin(), local_reverse_errors.end(), uint64_t{0});

  bool valid = format_errors == 0 && diagonal_errors == 0 &&
               padding_errors == 0 && cycle_type(root) == root_type &&
               list_errors == 0 && edge_errors == 0 &&
               reverse_edge_errors == 0;
  std::ofstream result(argv[8]);
  result << "{\n"
         << "  \"stored_vertices\": " << count << ",\n"
         << "  \"independently_enumerated_vertices\": " << expected_vertices.size() << ",\n"
         << "  \"candidate_list_errors\": " << list_errors << ",\n"
         << "  \"pairs_checked\": " << pairs << ",\n"
         << "  \"edges\": " << edges << ",\n"
         << "  \"edge_errors\": " << edge_errors << ",\n"
         << "  \"reverse_edge_errors\": " << reverse_edge_errors << ",\n"
         << "  \"format_errors\": " << format_errors << ",\n"
         << "  \"diagonal_errors\": " << diagonal_errors << ",\n"
         << "  \"padding_errors\": " << padding_errors << ",\n"
         << "  \"crossview_filter_level\": " << filter_level << ",\n"
         << "  \"workers\": " << workers << ",\n"
         << "  \"valid\": " << (valid ? "true" : "false") << "\n}\n";
  std::ofstream summary(argv[9]);
  summary << "Complete independent four-type graph audit\n\n"
          << "stored/enumerated vertices: " << count << '/'
          << expected_vertices.size() << '\n'
          << "candidate-list errors: " << list_errors << '\n'
          << "pairs/edges: " << pairs << '/' << edges << '\n'
          << "edge errors: " << edge_errors << '\n'
          << "reverse-edge errors: " << reverse_edge_errors << '\n'
          << "format/diagonal/padding errors: " << format_errors << '/'
          << diagonal_errors << '/' << padding_errors << '\n'
          << "cross-view filter level: " << filter_level << '\n'
          << "workers: " << workers << '\n'
          << "valid: " << (valid ? "true" : "false") << '\n';
  return valid ? 0 : 1;
}
