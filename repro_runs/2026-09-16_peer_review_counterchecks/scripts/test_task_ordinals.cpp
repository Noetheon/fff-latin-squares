#include <sstream>
#include <string>
#include "task_ordinals.hpp"

static void require(bool result) {
  if (!result) throw std::runtime_error("regression assertion failed");
}

static void rejects(const std::string& text) {
  std::istringstream input(text);
  bool rejected = false;
  try { select_task_ordinals({100,101,102}, input); }
  catch (const std::runtime_error&) { rejected = true; }
  require(rejected);
}

int main() {
  std::istringstream offset("0 1");
  require(select_task_ordinals({100,101,102}, offset) == std::vector<uint32_t>({100,101}));
  std::istringstream nonmonotone("0 1 2");
  require(select_task_ordinals({900,3,50}, nonmonotone) == std::vector<uint32_t>({900,3,50}));
  std::istringstream identity("0 2");
  require(select_task_ordinals({0,1,2}, identity) == std::vector<uint32_t>({0,2}));
  for (const auto& invalid : {"", "1 1", "2 1", "3", "-1", "4294967296", "0 x",
                              "0 4294967296", "0 1.5", "0 -1"})
    rejects(invalid);
}
