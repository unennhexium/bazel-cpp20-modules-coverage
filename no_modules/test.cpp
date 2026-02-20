#include <gtest/gtest.h>
#include "lib.h"

TEST(LibTest, HelloWorld) {
  EXPECT_EQ(greet(), "Hello, World!");
}
