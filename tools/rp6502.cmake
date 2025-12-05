# CMake Toolchain file for cc65.

# Select the target system.
set(CC65_TARGET rp6502)

# Find the executables we'll be using.
find_program(CMAKE_C_COMPILER cl65 REQUIRED)
find_program(CMAKE_ASM_COMPILER cl65 REQUIRED)
find_program(CMAKE_LINKER ld65 REQUIRED)
find_program(CMAKE_AR ar65 REQUIRED)
set(CC65_C_COMPILER "${CMAKE_C_COMPILER}" CACHE FILEPATH "Real cc65 C compiler")

# Add system include dir for analysis tools like IntelliSense.
execute_process(
    COMMAND ${CC65_C_COMPILER} --print-target-path
    OUTPUT_VARIABLE CC65_SYSTEM_INCLUDE_DIR
    OUTPUT_STRIP_TRAILING_WHITESPACE
)
cmake_path(APPEND CC65_SYSTEM_INCLUDE_DIR ".." "include")
cmake_path(ABSOLUTE_PATH CC65_SYSTEM_INCLUDE_DIR NORMALIZE)
include_directories(BEFORE SYSTEM ${CC65_SYSTEM_INCLUDE_DIR})

# Evil hack to get IntelliSense and problem matchers working by wrapping cl65.
# Comment out these lines to completely disable hack.
add_compile_options("$<$<COMPILE_LANGUAGE:C>:SHELL:-D__fastcall__=>")
add_compile_options("$<$<COMPILE_LANGUAGE:C>:SHELL:-D__cdecl__=>")
set(CMAKE_C_COMPILER ${CMAKE_COMMAND})
set(CMAKE_C_COMPILER_ARG1 "-P ${CMAKE_CURRENT_LIST_DIR}/cc65_wrapper.cmake -- ${CC65_C_COMPILER}")
set(CC65_ASM_COMPILER "${CMAKE_ASM_COMPILER}" CACHE FILEPATH "Real cc65 ASM compiler")
set(CMAKE_ASM_COMPILER ${CMAKE_COMMAND})
set(CMAKE_ASM_COMPILER_ARG1 "-P ${CMAKE_CURRENT_LIST_DIR}/cc65_wrapper.cmake -- ${CC65_ASM_COMPILER}")

# Override CMake internals to work with cc65.
set(CMAKE_SYSTEM_NAME Generic)
set(CMAKE_C_COMPILE_OBJECT "<CMAKE_C_COMPILER> <DEFINES> <INCLUDES> <FLAGS> -o <OBJECT> --add-source -l <OBJECT>.s -c <SOURCE>")
set(CMAKE_C_CREATE_STATIC_LIBRARY "<CMAKE_AR> a <TARGET> <LINK_FLAGS> <OBJECTS>")
set(CMAKE_C_FLAGS "--target ${CC65_TARGET}")
set(CMAKE_C_FLAGS_DEBUG_INIT "-O")
set(CMAKE_C_FLAGS_RELEASE_INIT "-Oirs")
set(CMAKE_C_LINK_EXECUTABLE "<CMAKE_C_COMPILER> <FLAGS> <CMAKE_C_LINK_FLAGS> <LINK_FLAGS> <OBJECTS> -o <TARGET> -m <TARGET>.map <LINK_LIBRARIES>")
set(CMAKE_C_ABI_COMPILED 0)
set(CMAKE_C_COMPILER_WORKS 1)
set(CMAKE_ASM_CREATE_STATIC_LIBRARY ${CMAKE_C_CREATE_STATIC_LIBRARY})
set(CMAKE_ASM_FLAGS "--target ${CC65_TARGET}")
set(CMAKE_ASM_LINK_EXECUTABLE "<CMAKE_ASM_COMPILER> <FLAGS> <CMAKE_ASM_LINK_FLAGS> <LINK_FLAGS> <OBJECTS> -o <TARGET> -m <TARGET>.map <LINK_LIBRARIES>")
