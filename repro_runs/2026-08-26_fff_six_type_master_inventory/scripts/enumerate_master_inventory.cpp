#include <algorithm>
#include <array>
#include <cstdint>
#include <iostream>
#include <map>
#include <numeric>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

#include "partial_cycle.hpp"

using Perm = std::array<uint8_t, 10>;

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

static uint64_t type_code(std::initializer_list<int> lengths) {
  uint64_t code = 0;
  for (int length : lengths) code += uint64_t{1} << (4 * length);
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

static Perm conjugate(const Perm &g, const Perm &permutation) {
  return compose(compose(g, permutation), inverse(g));
}

static uint64_t key(const Perm &permutation) {
  uint64_t result = 0;
  for (int point = 0; point < 10; ++point) {
    result |= uint64_t{permutation[point]} << (4 * point);
  }
  return result;
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

static void run(const std::string &label, const Perm &root,
                const std::vector<uint64_t> &allowed) {
  Perm identity{};
  std::iota(identity.begin(), identity.end(), 0);
  const Perm inverse_root = inverse(root);
  Perm candidate = identity;
  uint64_t class_allowed = 0;
  uint64_t triple_allowed = 0;
  std::array<uint64_t, 10> bucket_counts{};
  std::vector<Perm> candidates;
  do {
    const uint64_t first = cycle_code(candidate);
    const uint64_t second = cycle_code(compose(candidate, inverse_root));
    if (std::find(allowed.begin(), allowed.end(), first) == allowed.end() ||
        std::find(allowed.begin(), allowed.end(), second) == allowed.end()) {
      continue;
    }
    ++class_allowed;
    if (creates_crossview_odd_cycle({identity, root, candidate})) continue;
    ++triple_allowed;
    ++bucket_counts[candidate[0]];
    candidates.push_back(candidate);
  } while (std::next_permutation(candidate.begin(), candidate.end()));

  std::vector<Perm> group;
  Perm g = identity;
  do {
    if (g[0] == 0 && g[2] == 2 && conjugate(g, root) == root) {
      group.push_back(g);
    }
  } while (std::next_permutation(g.begin(), g.end()));

  std::unordered_map<uint64_t, size_t> index;
  index.reserve(candidates.size() * 2);
  for (size_t position = 0; position < candidates.size(); ++position) {
    index.emplace(key(candidates[position]), position);
  }
  std::unordered_set<size_t> remaining;
  for (size_t position = 0; position < candidates.size(); ++position) {
    if (candidates[position][0] == 2) remaining.insert(position);
  }
  std::map<size_t, size_t> orbit_sizes;
  while (!remaining.empty()) {
    const size_t seed = *remaining.begin();
    std::unordered_set<size_t> orbit;
    for (const Perm &element : group) {
      const auto found = index.find(key(conjugate(element, candidates[seed])));
      if (found == index.end() || candidates[found->second][0] != 2) {
        throw std::runtime_error("residual orbit escaped candidate bucket");
      }
      orbit.insert(found->second);
    }
    ++orbit_sizes[orbit.size()];
    for (size_t position : orbit) remaining.erase(position);
  }

  const uint64_t words = (triple_allowed + 63) / 64;
  const uint64_t graph_bytes = 26 + 10 * triple_allowed
      + 8 * triple_allowed * words;
  std::cout << label << '\n'
            << "class_allowed=" << class_allowed << '\n'
            << "triple_allowed=" << triple_allowed << '\n'
            << "bucket_counts=";
  for (int value = 0; value < 10; ++value) {
    if (value) std::cout << ',';
    std::cout << bucket_counts[value];
  }
  std::cout << '\n'
            << "residual_group_size=" << group.size() << '\n'
            << "root_task_count=" << bucket_counts[2] << '\n'
            << "orbit_size_counts=";
  bool first_orbit = true;
  size_t orbit_count = 0;
  for (const auto &[size, count] : orbit_sizes) {
    if (!first_orbit) std::cout << ',';
    std::cout << size << ':' << count;
    first_orbit = false;
    orbit_count += count;
  }
  std::cout << '\n'
            << "orbit_count=" << orbit_count << '\n'
            << "dense_graph_bytes=" << graph_bytes << '\n';
}

int main() {
  const std::vector<uint64_t> all_f{
      type_code({10}), type_code({2,2,2,2,2}), type_code({4,2,2,2}),
      type_code({4,4,2}), type_code({6,2,2}), type_code({6,4}),
      type_code({8,2})};
  std::vector<uint64_t> non_involution = all_f;
  non_involution.erase(non_involution.begin() + 1);

  const Perm involution_root{1,0,3,2,5,4,7,6,9,8};
  const Perm even_root{1,2,3,0,5,4,7,6,9,8};
  run("involution_master_all_7_types", involution_root, all_f);
  run("noninvolution_master_6_types", even_root, non_involution);
}
