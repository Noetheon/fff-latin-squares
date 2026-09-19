#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <map>
#include <numeric>
#include <set>
#include <string>
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

static Perm conjugate(const Perm &g, const Perm &q) {
  return compose(compose(g, q), inverse(g));
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

static bool creates_crossview_odd_cycle(const std::array<Perm, 3> &rows) {
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

static int rank_perm(const Perm &permutation) {
  static const int factorial[10] = {1,1,2,6,24,120,720,5040,40320,362880};
  int rank = 0;
  for (int i = 0; i < 10; ++i) {
    int smaller = 0;
    for (int j = i + 1; j < 10; ++j) smaller += permutation[j] < permutation[i];
    rank += smaller * factorial[9 - i];
  }
  return rank;
}

int main(int argc, char **argv) {
  if (argc != 10) {
    std::cerr << "usage: dimension CASE TYPE1 TYPE2 TYPE3 TYPE4 TYPE5 ROOT JSON SUMMARY\n";
    return 2;
  }
  std::string case_id = argv[1];
  std::vector<Type> palette{parse_type(argv[2]), parse_type(argv[3]),
      parse_type(argv[4]), parse_type(argv[5]), parse_type(argv[6])};
  Type root_type = parse_type(argv[7]);
  if (!allowed(root_type, palette)) return 3;
  Perm identity{};
  std::iota(identity.begin(), identity.end(), 0);
  Perm root = representative(root_type);
  Perm inverse_root = inverse(root);

  std::vector<Perm> vertices;
  std::array<uint32_t, 8> bucket_sizes{};
  uint64_t unfiltered = 0;
  Perm candidate = identity;
  do {
    if (!allowed(cycle_type(candidate), palette) ||
        !allowed(cycle_type(compose(candidate, inverse_root)), palette)) continue;
    ++unfiltered;
    if (creates_crossview_odd_cycle({identity, root, candidate})) continue;
    int bucket = candidate[0] - 2;
    if (bucket < 0 || bucket >= 8) return 4;
    ++bucket_sizes[bucket];
    vertices.push_back(candidate);
  } while (std::next_permutation(candidate.begin(), candidate.end()));

  int initial_bucket = 0;
  for (int bucket = 1; bucket < 8; ++bucket) {
    if (bucket_sizes[bucket] < bucket_sizes[initial_bucket]) initial_bucket = bucket;
  }
  int initial_image = initial_bucket + 2;
  std::vector<Perm> group;
  Perm g = identity;
  do {
    if (g[0] == 0 && g[initial_image] == initial_image &&
        compose(g, root) == compose(root, g)) group.push_back(g);
  } while (std::next_permutation(g.begin(), g.end()));

  std::vector<int32_t> index_by_rank(3628800, -1);
  for (uint32_t index = 0; index < vertices.size(); ++index) {
    int rank = rank_perm(vertices[index]);
    if (index_by_rank[rank] >= 0) return 5;
    index_by_rank[rank] = index;
  }
  std::vector<uint32_t> tasks;
  std::vector<int32_t> task_ordinal(vertices.size(), -1);
  for (uint32_t index = 0; index < vertices.size(); ++index) {
    if (vertices[index][0] == initial_image) {
      task_ordinal[index] = tasks.size();
      tasks.push_back(index);
    }
  }

  std::vector<bool> covered(tasks.size());
  std::vector<uint32_t> representatives;
  std::map<uint32_t, uint32_t> orbit_size_counts;
  uint64_t orbit_union_total = 0;
  bool orbit_escape = false;
  for (uint32_t ordinal = 0; ordinal < tasks.size(); ++ordinal) {
    if (covered[ordinal]) continue;
    std::set<uint32_t> orbit;
    for (const Perm &element : group) {
      Perm image = conjugate(element, vertices[tasks[ordinal]]);
      int32_t index = index_by_rank[rank_perm(image)];
      if (index < 0 || task_ordinal[index] < 0) {
        orbit_escape = true;
        continue;
      }
      orbit.insert(task_ordinal[index]);
    }
    representatives.push_back(*orbit.begin());
    ++orbit_size_counts[orbit.size()];
    orbit_union_total += orbit.size();
    for (uint32_t item : orbit) covered[item] = true;
  }
  uint64_t covered_count = std::count(covered.begin(), covered.end(), true);
  bool valid = !orbit_escape && covered_count == tasks.size() &&
               orbit_union_total == tasks.size();

  std::ofstream json(argv[8]);
  json << "{\n  \"schema_version\": \"five-type-root-orbit-dimension-v1\",\n"
       << "  \"case_id\": \"" << case_id << "\",\n  \"palette\": [";
  for (int i = 0; i < 5; ++i) {
    if (i) json << ',';
    json << '"' << argv[2 + i] << '"';
  }
  json << "],\n  \"root_type\": \"" << argv[7] << "\",\n"
       << "  \"unfiltered_candidates\": " << unfiltered << ",\n"
       << "  \"level1_candidates\": " << vertices.size() << ",\n"
       << "  \"bucket_sizes\": [";
  for (int i = 0; i < 8; ++i) { if (i) json << ','; json << bucket_sizes[i]; }
  json << "],\n  \"initial_bucket\": " << initial_bucket << ",\n"
       << "  \"initial_image\": " << initial_image << ",\n"
       << "  \"residual_group_size\": " << group.size() << ",\n"
       << "  \"full_initial_tasks\": " << tasks.size() << ",\n"
       << "  \"orbit_count\": " << representatives.size() << ",\n"
       << "  \"orbit_size_counts\": {";
  bool first = true;
  for (auto [size, count] : orbit_size_counts) {
    if (!first) json << ',';
    first = false;
    json << '"' << size << "\":" << count;
  }
  json << "},\n  \"covered_tasks\": " << covered_count << ",\n"
       << "  \"orbit_union_total\": " << orbit_union_total << ",\n"
       << "  \"orbit_escape\": " << (orbit_escape ? "true" : "false") << ",\n"
       << "  \"representative_task_ordinals\": [";
  for (size_t i = 0; i < representatives.size(); ++i) {
    if (i) json << ',';
    json << representatives[i];
  }
  json << "],\n  \"valid\": " << (valid ? "true" : "false") << "\n}\n";

  std::ofstream summary(argv[9]);
  summary << case_id << " root " << argv[7] << '\n'
          << "unfiltered/level1 candidates: " << unfiltered << '/' << vertices.size() << '\n'
          << "initial tasks: " << tasks.size() << '\n'
          << "residual group/orbits: " << group.size() << '/' << representatives.size() << '\n'
          << "covered tasks: " << covered_count << '\n'
          << "valid: " << (valid ? "true" : "false") << '\n';
  return valid ? 0 : 1;
}
