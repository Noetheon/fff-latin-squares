#include <algorithm>
#include <array>
#include <chrono>
#include <fstream>
#include <iostream>
#include <numeric>
#include <string>
#include <vector>

using Perm = std::array<unsigned char, 10>;
using Type = std::vector<int>;

static const std::vector<Type> types = {
    {10}, {2, 2, 2, 2, 2}, {4, 2, 2, 2}, {4, 4, 2},
    {6, 2, 2}, {6, 4}, {8, 2}};

static std::string name(const Type &type) {
  std::string result;
  for (size_t index = 0; index < type.size(); ++index) {
    if (index) result += '+';
    result += std::to_string(type[index]);
  }
  return result;
}

static Type kind(const Perm &permutation) {
  std::array<bool, 10> seen{};
  Type result;
  for (int start = 0; start < 10; ++start) {
    if (seen[start]) continue;
    int current = start;
    int length = 0;
    do {
      seen[current] = true;
      current = permutation[current];
      ++length;
    } while (current != start);
    result.push_back(length);
  }
  std::sort(result.rbegin(), result.rend());
  return result;
}

static int type_id(const Perm &permutation) {
  Type type = kind(permutation);
  for (int index = 0; index < 7; ++index) {
    if (types[index] == type) return index;
  }
  return -1;
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

int main(int argc, char **argv) {
  if (argc != 3) return 2;
  auto started = std::chrono::steady_clock::now();
  static uint64_t counts[7][7][7][10]{};
  for (int root = 0; root < 7; ++root) {
    Perm root_inverse = inverse(representative(types[root]));
    Perm candidate{};
    std::iota(candidate.begin(), candidate.end(), 0);
    do {
      int left_type = type_id(candidate);
      int right_type = type_id(compose(candidate, root_inverse));
      if (left_type >= 0 && right_type >= 0) {
        ++counts[root][left_type][right_type][candidate[0]];
      }
    } while (std::next_permutation(candidate.begin(), candidate.end()));
  }

  std::ofstream json(argv[1]);
  std::ofstream summary(argv[2]);
  json << "{\n  \"degree\": 10,\n  \"records\": [\n";
  summary << "Actual four-type candidate dimensions\n\n";
  bool first = true;
  int case_number = 0;
  for (int a = 0; a < 7; ++a) for (int b = a + 1; b < 7; ++b)
  for (int c = b + 1; c < 7; ++c) for (int d = c + 1; d < 7; ++d) {
    ++case_number;
    std::array<int, 4> palette{a, b, c, d};
    for (int root : palette) {
      std::array<uint64_t, 10> buckets{};
      for (int left : palette) for (int right : palette) {
        for (int image = 0; image < 10; ++image) {
          buckets[image] += counts[root][left][right][image];
        }
      }
      uint64_t total = 0;
      for (int image = 2; image < 10; ++image) total += buckets[image];
      if (!first) json << ",\n";
      first = false;
      json << "    {\"case_id\": \"p" << (case_number < 10 ? "0" : "")
           << case_number << "\", \"palette\": [";
      for (int index = 0; index < 4; ++index) {
        if (index) json << ", ";
        json << '\"' << name(types[palette[index]]) << '\"';
      }
      json << "], \"root_type\": \"" << name(types[root])
           << "\", \"candidate_vertices\": " << total
           << ", \"bucket_counts\": [";
      for (int image = 2; image < 10; ++image) {
        if (image > 2) json << ", ";
        json << buckets[image];
      }
      json << "]}";
    }
  }
  double elapsed = std::chrono::duration<double>(
      std::chrono::steady_clock::now() - started).count();
  json << "\n  ],\n  \"elapsed_seconds\": " << elapsed << "\n}\n";
  summary << "cases: 35\nroot records: 140\nelapsed seconds: " << elapsed << '\n';
}
