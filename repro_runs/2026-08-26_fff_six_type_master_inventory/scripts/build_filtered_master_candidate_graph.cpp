#include <algorithm>
#include <array>
#include <atomic>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <numeric>
#include <string>
#include <thread>
#include <vector>

#include "partial_cycle.hpp"

using Perm = std::array<uint8_t, 10>;
using Type = std::vector<int>;

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

static Perm compose(const Perm &left, const Perm &right) {
  Perm result{};
  for (int point = 0; point < 10; ++point) result[point] = left[right[point]];
  return result;
}

static Perm relative(const Perm &left, const Perm &right) {
  return compose(right, inverse(left));
}

static Perm relative_from_inverse(const Perm &inverse_left, const Perm &right) {
  return compose(right, inverse_left);
}

static Perm representative(const Type &type) {
  Perm result{};
  int start = 0;
  for (int length : type) {
    for (int offset = 0; offset < length; ++offset) {
      result[start + offset] = start + (offset + 1) % length;
    }
    start += length;
  }
  return result;
}

static bool allowed(const Type &type, const std::vector<Type> &palette) {
  return std::find(palette.begin(), palette.end(), type) != palette.end();
}

static bool allowed_code(uint64_t code, const std::vector<uint64_t> &palette) {
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

static void write_u32(std::ofstream &output, uint32_t value) {
  output.write(reinterpret_cast<const char *>(&value), sizeof(value));
}

int main(int argc, char **argv) {
  if (argc < 12) {
    std::cerr << "usage: build ROOT FILTER_LEVEL GRAPH SUMMARY LABEL WORKERS TYPE1 ... TYPEN\n";
    return 2;
  }
  Type root_type = parse_type(argv[1]);
  int filter_level = std::stoi(argv[2]);
  int workers = std::max(1, std::stoi(argv[6]));
  std::vector<Type> palette;
  std::vector<uint64_t> palette_codes;
  for (int index = 7; index < argc; ++index) {
    Type type = parse_type(argv[index]);
    palette_codes.push_back(type_code(type));
    palette.push_back(std::move(type));
  }
  if (!allowed(root_type, palette)) return 3;

  Perm identity{};
  std::iota(identity.begin(), identity.end(), 0);
  Perm root = representative(root_type);
  Perm inverse_root = inverse(root);
  Perm candidate = identity;
  std::vector<Perm> vertices;
  uint64_t unfiltered_candidates = 0;
  std::array<uint32_t, 8> bucket_counts{};
  do {
    if (!allowed_code(cycle_code(candidate), palette_codes) ||
        !allowed_code(cycle_code(relative_from_inverse(inverse_root, candidate)), palette_codes)) {
      continue;
    }
    ++unfiltered_candidates;
    if (filter_level >= 1 && creates_crossview_odd_cycle(
            std::array<Perm, 3>{identity, root, candidate})) continue;
    ++bucket_counts[candidate[0] - 2];
    vertices.push_back(candidate);
  } while (std::next_permutation(candidate.begin(), candidate.end()));

  uint32_t count = vertices.size();
  std::vector<Perm> inverse_vertices(count);
  for (uint32_t index = 0; index < count; ++index) {
    inverse_vertices[index] = inverse(vertices[index]);
  }
  uint32_t words = (count + 63) / 64;
  std::vector<std::vector<uint64_t>> adjacency(
      count, std::vector<uint64_t>(words));
  uint64_t edges = 0;
  if (workers == 1) {
    for (uint32_t left = 0; left < count; ++left) {
      for (uint32_t right = left + 1; right < count; ++right) {
        if (!allowed_code(cycle_code(relative_from_inverse(
                inverse_vertices[left], vertices[right])), palette_codes)) continue;
        if (filter_level >= 2 && creates_crossview_odd_cycle(
                std::array<Perm, 4>{identity, root, vertices[left], vertices[right]})) {
          continue;
        }
        adjacency[left][right / 64] |= uint64_t{1} << (right % 64);
        adjacency[right][left / 64] |= uint64_t{1} << (left % 64);
        ++edges;
      }
    }
  } else {
    std::atomic<uint32_t> next_left{0};
    std::vector<uint64_t> directed_edges(workers);
    auto build_rows = [&](int worker) {
      while (true) {
        uint32_t left = next_left.fetch_add(1);
        if (left >= count) break;
        for (uint32_t right = 0; right < count; ++right) {
          if (left == right ||
              !allowed_code(cycle_code(relative_from_inverse(
                  inverse_vertices[left], vertices[right])), palette_codes)) {
            continue;
          }
          if (filter_level >= 2 && creates_crossview_odd_cycle(
                  std::array<Perm, 4>{identity, root, vertices[left], vertices[right]})) {
            continue;
          }
          adjacency[left][right / 64] |= uint64_t{1} << (right % 64);
          ++directed_edges[worker];
        }
      }
    };
    std::vector<std::thread> pool;
    for (int worker = 0; worker < workers; ++worker) pool.emplace_back(build_rows, worker);
    for (auto &thread : pool) thread.join();
    edges = std::accumulate(directed_edges.begin(), directed_edges.end(), uint64_t{0}) / 2;
  }

  std::ofstream output(argv[3], std::ios::binary);
  output.write("O8HTv1\0", 8);
  write_u32(output, count);
  write_u32(output, words);
  output.write(reinterpret_cast<const char *>(root.data()), root.size());
  for (const auto &vertex : vertices) {
    output.write(reinterpret_cast<const char *>(vertex.data()), vertex.size());
  }
  for (const auto &row : adjacency) {
    output.write(reinterpret_cast<const char *>(row.data()),
                 row.size() * sizeof(uint64_t));
  }

  std::ofstream summary(argv[4]);
  summary << "Filtered variable-palette candidate graph\n\n"
          << "label: " << argv[5] << '\n'
          << "palette:";
  for (int index = 7; index < argc; ++index) summary << ' ' << argv[index];
  summary << '\n'
          << "root: " << argv[1] << '\n'
          << "cross-view filter level: " << filter_level << '\n'
          << "workers: " << workers << '\n'
          << "unfiltered candidates: " << unfiltered_candidates << '\n'
          << "stored vertices: " << count << '\n'
          << "bucket counts:";
  for (uint32_t bucket_count : bucket_counts) summary << ' ' << bucket_count;
  summary << "\nedges: " << edges << '\n';
}
