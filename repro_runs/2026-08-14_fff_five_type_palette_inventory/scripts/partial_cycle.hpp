#pragma once

#include <array>
#include <cstdint>

namespace order8 {

inline bool partial_map_has_odd_cycle(const std::array<int8_t, 10> &map) {
  for (int start = 0; start < 10; ++start) {
    if (map[start] < 0) continue;
    std::array<int8_t, 10> position{};
    position.fill(-1);
    int current = start;
    int step = 0;
    while (current >= 0 && position[current] < 0) {
      position[current] = step++;
      current = map[current];
    }
    if (current >= 0) {
      int length = step - position[current];
      if (length > 1 && (length & 1)) return true;
    }
  }
  return false;
}

}  // namespace order8
