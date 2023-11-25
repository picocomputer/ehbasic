cmake_minimum_required(VERSION 3.13)

project(MY-RP6502-PROJECT C ASM)

add_subdirectory(tools)

add_executable(hello)
rp6502_executable(hello
    START 0xD000
    RESET 0xD000
    ${CMAKE_CURRENT_LIST_DIR}/src/help.rp6502
)
target_sources(hello PRIVATE
    src/min_mon.asm
)
