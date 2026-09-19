#pragma once
#include <charconv>
#include <cstdint>
#include <istream>
#include <stdexcept>
#include <string>
#include <vector>

inline std::vector<uint32_t> select_task_ordinals(
    const std::vector<uint32_t>& tasks, std::istream& input) {
  std::vector<uint32_t> selected;
  uint32_t previous_ordinal = 0;
  std::string token;
  while (input >> token) {
    uint32_t ordinal = 0;
    auto parsed = std::from_chars(token.data(), token.data()+token.size(), ordinal);
    if (parsed.ec != std::errc{} || parsed.ptr != token.data()+token.size())
      throw std::runtime_error("invalid task ordinal");
    if (ordinal >= tasks.size())
      throw std::runtime_error("task ordinal out of range");
    if (!selected.empty() && ordinal <= previous_ordinal)
      throw std::runtime_error("task ordinals not strictly increasing");
    selected.push_back(tasks[ordinal]);
    previous_ordinal = ordinal;
  }
  if (input.bad() || !input.eof() || selected.empty())
    throw std::runtime_error("invalid or empty task ordinal file");
  return selected;
}
