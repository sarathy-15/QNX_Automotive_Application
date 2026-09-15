#ifndef MCP2515_SPI_TEST_H
#define MCP2515_SPI_TEST_H

#ifdef __cplusplus
extern "C" {
#endif

/*
 * Run a basic MCP2515 SPI hardware test.
 *
 * Test sequence:
 *  1. Open /dev/io-spi/spi0/dev0
 *  2. Configure SPI mode 0, 1 MHz
 *  3. Send MCP2515 RESET command
 *  4. Read CANSTAT
 *  5. Read CANCTRL
 *  6. Verify MCP2515 is in Configuration mode
 *
 * Returns:
 *   0  = PASS
 *  -1  = FAIL
 */
int mcp2515_spi_test(void);

#ifdef __cplusplus
}
#endif

#endif
