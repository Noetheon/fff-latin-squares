#include <bit>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

static uint32_t read_u32(std::ifstream &input) {
  uint32_t value;
  input.read(reinterpret_cast<char *>(&value), sizeof(value));
  return value;
}

int main(int argc, char **argv) {
  if (argc != 3) {
    std::cerr << "usage: export_partite_graph_dimacs INPUT_BIN OUTPUT_DIMACS\n";
    return 2;
  }
  std::ifstream input(argv[1], std::ios::binary);
  char magic[8];
  input.read(magic, 8);
  if (!input || std::string(magic, 6) != "O8HTv1") return 3;
  uint32_t count = read_u32(input);
  uint32_t words = read_u32(input);
  input.seekg(10 + static_cast<std::streamoff>(count) * 10, std::ios::cur);
  std::vector<std::vector<uint64_t>> adjacency(
      count, std::vector<uint64_t>(words));
  uint64_t directed_edges = 0;
  for (auto &row : adjacency) {
    input.read(reinterpret_cast<char *>(row.data()), row.size() * sizeof(uint64_t));
    for (uint64_t word : row) directed_edges += std::popcount(word);
  }
  if (!input || input.peek() != std::ifstream::traits_type::eof()) return 4;
  if (directed_edges % 2) return 5;
  uint64_t edges = directed_edges / 2;
  std::ofstream output(argv[2]);
  output << "p edge " << count << ' ' << edges << '\n';
  for (uint32_t left = 0; left < count; ++left) {
    for (uint32_t right = left + 1; right < count; ++right) {
      if (adjacency[left][right / 64] & (uint64_t{1} << (right % 64))) {
        output << "e " << left + 1 << ' ' << right + 1 << '\n';
      }
    }
  }
  std::cout << "vertices=" << count << " edges=" << edges << '\n';
  return output ? 0 : 6;
}
