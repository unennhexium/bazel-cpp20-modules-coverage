#include <gtest/gtest.h>

import lib;

TEST(LibTest, HelloWorld) {
  EXPECT_EQ(greet(), "Hello, World!");
}
