#include <iostream>
#include <format> // 
#include <string>

int main() {
    std::string name = "yassine";
    std::cout << std::format("Hello, my name is {}\n", name);
    return 1;
}
