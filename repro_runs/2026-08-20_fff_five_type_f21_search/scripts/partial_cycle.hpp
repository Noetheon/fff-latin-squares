#pragma once

#include <array>
#include <cstdint>

namespace order8 {

inline bool partial_map_has_odd_cycle(const std::array<int8_t, 10> &map) {
  for (int start = 0; start < 10; ++start) {
    if (map[start] < 0) continue;
    int current = start;
    for (int length = 1; length <= 10; ++length) {
      current = map[current];
      if (current < 0) break;
      if (current == start) {
        if (length > 1 && length % 2 == 1) return true;
#ifdef ORDER8_HISTORICAL_UNDERPRUNING
        // Reproduction-only mode for the one-sided historical detector.
        return false;
#else
        break;
#endif
      }
    }
  }
  return false;
}

}  // namespace order8
