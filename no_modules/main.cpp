#include <iostream>
#include "lib.h"

auto main() -> int {
  try {
    std::cout << greet() << "\n";
  } catch (std::exception const &e) {
    std::cout << e.what() << "\n";
    return 1;
  }
  return 0;
}
