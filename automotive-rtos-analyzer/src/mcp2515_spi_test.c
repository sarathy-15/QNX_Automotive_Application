/*
 * mcp2515_spi_test.c
 *
 * Standalone MCP2515 SPI communication test for QNX / Raspberry Pi.
 *
 * IMPORTANT:
 * This file contains ONLY the standalone SPI test.
 * It must NOT contain can_interface_*() or mcp2515_configure()
 * implementations, because those functions belong to can_interface.c.
 */

#include "mcp2515_spi_test.h"

#include <stdio.h>
#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include <devctl.h>
#include <hw/io-spi.h>

/* QNX SPI device */
#define MCP2515_SPI_DEVICE   "/dev/io-spi/spi0/dev0"
#define MCP2515_SPI_CLOCK    1000000U

/* MCP2515 commands */
#define MCP2515_CMD_RESET    0xC0U
#define MCP2515_CMD_READ     0x03U

/* MCP2515 registers */
#define MCP2515_CANSTAT      0x0EU
#define MCP2515_CANCTRL      0x0FU

/*
 * Perform one full-duplex SPI transfer.
 *
 * This follows the known-working QNX SPI transfer pattern:
 * spi_xchng_t is supplied by <hw/io-spi.h>.
 */
static int spi_transfer(int fd,
                        const uint8_t *tx,
                        uint8_t *rx,
                        size_t length)
{
    size_t msg_size;
    spi_xchng_t *msg;
    int status;

    if (fd < 0 || tx == NULL || rx == NULL || length == 0U) {
        return EINVAL;
    }

    msg_size = sizeof(spi_xchng_t) + length;

    msg = (spi_xchng_t *)malloc(msg_size);
    if (msg == NULL) {
        return ENOMEM;
    }

    memset(msg, 0, msg_size);

    msg->nbytes = (uint32_t)length;
    memcpy(msg->data, tx, length);

    status = devctl(fd,
                    DCMD_SPI_DATA_XCHNG,
                    msg,
                    msg_size,
                    NULL);

    if (status == EOK) {
        memcpy(rx, msg->data, length);
    }

    free(msg);

    return status;
}

/*
 * Configure SPI:
 *   Mode 0
 *   1 MHz
 *
 * Word width / bit order are provided by the QNX SPI configuration.
 */
static int spi_configure(int fd)
{
    spi_cfg_t cfg;
    int status;

    memset(&cfg, 0, sizeof(cfg));

    cfg.mode = 0U;
    cfg.clock_rate = MCP2515_SPI_CLOCK;

    status = devctl(fd,
                    DCMD_SPI_SET_CONFIG,
                    &cfg,
                    sizeof(cfg),
                    NULL);

    if (status != EOK) {
        printf("[MCP2515 TEST] SPI configuration failed: %s\n",
               strerror(status));
        return status;
    }

    printf("[MCP2515 TEST] SPI configured: Mode 0, %u Hz\n",
           MCP2515_SPI_CLOCK);

    return EOK;
}

/*
 * Send MCP2515 RESET command.
 */
static int mcp2515_reset_command(int fd)
{
    uint8_t tx[1];
    uint8_t rx[1];
    int status;

    tx[0] = MCP2515_CMD_RESET;
    rx[0] = 0U;

    printf("[MCP2515 TEST] Sending MCP2515 RESET...\n");

    status = spi_transfer(fd, tx, rx, sizeof(tx));

    if (status != EOK) {
        printf("[MCP2515 TEST] RESET transfer failed: %s\n",
               strerror(status));
        return status;
    }

    /*
     * MCP2515 needs a short time after RESET before register access.
     */
    usleep(10000);

    printf("[MCP2515 TEST] RESET command successful\n");

    return EOK;
}

/*
 * Read one MCP2515 register.
 */
static int mcp2515_read_register(int fd,
                                 uint8_t address,
                                 uint8_t *value)
{
    uint8_t tx[3];
    uint8_t rx[3];
    int status;

    if (value == NULL) {
        return EINVAL;
    }

    tx[0] = MCP2515_CMD_READ;
    tx[1] = address;
    tx[2] = 0U;

    rx[0] = 0U;
    rx[1] = 0U;
    rx[2] = 0U;

    status = spi_transfer(fd, tx, rx, sizeof(tx));

    if (status != EOK) {
        printf("[MCP2515 TEST] Register 0x%02X read failed: %s\n",
               address,
               strerror(status));
        return status;
    }

    *value = rx[2];

    return EOK;
}

/*
 * Public standalone MCP2515 SPI test.
 *
 * Expected result after RESET:
 * CANSTAT OPMOD bits [7:5] = 100b
 * Therefore:
 *     (CANSTAT & 0xE0) == 0x80
 */
int mcp2515_spi_test(void)
{
    int fd;
    int status;
    uint8_t canstat;
    uint8_t canctrl;

    printf("\n");
    printf("========================================\n");
    printf("      MCP2515 SPI COMMUNICATION TEST\n");
    printf("========================================\n");

    printf("[MCP2515 TEST] Opening SPI device: %s\n",
           MCP2515_SPI_DEVICE);

    fd = open(MCP2515_SPI_DEVICE, O_RDWR);

    if (fd == -1) {
        printf("[MCP2515 TEST] SPI open failed: %s\n",
               strerror(errno));
        printf("[MCP2515 TEST] Check QNX SPI driver/device path.\n");
        return -1;
    }

    printf("[MCP2515 TEST] SPI FD = %d\n", fd);

    status = spi_configure(fd);

    if (status != EOK) {
        close(fd);
        return -1;
    }

    status = mcp2515_reset_command(fd);

    if (status != EOK) {
        close(fd);
        return -1;
    }

    /*
     * Read CANSTAT after RESET.
     */
    status = mcp2515_read_register(fd,
                                   MCP2515_CANSTAT,
                                   &canstat);

    if (status != EOK) {
        printf("[MCP2515 TEST] CANSTAT read failed\n");
        close(fd);
        return -1;
    }

    printf("[MCP2515 TEST] CANSTAT = 0x%02X\n", canstat);

    /*
     * Read CANCTRL as an additional communication check.
     */
    status = mcp2515_read_register(fd,
                                   MCP2515_CANCTRL,
                                   &canctrl);

    if (status != EOK) {
        printf("[MCP2515 TEST] CANCTRL read failed\n");
        close(fd);
        return -1;
    }

    printf("[MCP2515 TEST] CANCTRL = 0x%02X\n", canctrl);

    /*
     * After RESET, MCP2515 should be in Configuration mode.
     * OPMOD bits are bits 7:5 and should equal 100b = 0x80.
     */
    if ((canstat & 0xE0U) == 0x80U) {
        printf("\n");
        printf("========================================\n");
        printf("       MCP2515 SPI TEST : PASSED\n");
        printf("========================================\n");
        printf("CANSTAT configuration mode verified.\n");
        printf("MCP2515 SPI communication is working.\n");
        printf("\n");

        close(fd);
        return 0;
    }

    printf("\n");
    printf("========================================\n");
    printf("       MCP2515 SPI TEST : FAILED\n");
    printf("========================================\n");
    printf("Unexpected CANSTAT value: 0x%02X\n", canstat);
    printf("Expected Configuration mode (OPMOD = 100b).\n");
    printf("Check MCP2515 power, SPI wiring, CS, MISO/MOSI,\n");
    printf("level shifter and SPI device configuration.\n");
    printf("\n");

    close(fd);

    return -1;
}
