cmake_minimum_required(VERSION 3.13)

project(EHBASIC-RP6502-PROJECT C ASM)

add_subdirectory(tools)

add_executable(basic)
rp6502_executable(basic
    START 0xD000
    RESET 0xD000
    ${CMAKE_CURRENT_LIST_DIR}/doc/help.rp6502
)
target_sources(basic PRIVATE
    src/basic.s
    src/main.c
    src/min_mon.s
)
