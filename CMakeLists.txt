cmake_minimum_required(VERSION 3.13)

project(EHBASIC-RP6502-PROJECT C ASM)

add_subdirectory(tools)

add_executable(basic)
rp6502_executable(basic
    START 0xD000
    RESET 0xD000
    IRQ 0xD002
    NMI 0xD00C
    ${CMAKE_CURRENT_SOURCE_DIR}/doc/help.rp6502
)
target_link_options(basic PRIVATE
    -C ${CMAKE_CURRENT_SOURCE_DIR}/src/rp6502.cfg
)
target_sources(basic PRIVATE
    src/basic.s
    src/head.s
    src/main.s
    src/min_mon.s
    src/usr.s
)
