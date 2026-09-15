/*
 * Automotive RTOS Performance & Latency Analyzer
 *
 * CAN Interface Implementation
 * Controller : MCP2515
 * Transceiver: TJA1050
 *
 * Step 13 - Real MCP2515 CAN Integration
 */

#include "can_interface.h"

#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <stdint.h>
#include <time.h>
#include <fcntl.h>
#include <errno.h>
#include <stdlib.h>

#include <devctl.h>
#include <hw/io-spi.h>

/* ============================================================
 * QNX SPI Configuration
 * ============================================================ */

#define MCP2515_SPI_DEVICE "/dev/io-spi/spi0/dev0"
#define MCP2515_SPI_CLOCK  1000000U

/* ============================================================
 * MCP2515 SPI Commands
 * ============================================================ */

#define MCP2515_CMD_RESET        0xC0
#define MCP2515_CMD_READ         0x03
#define MCP2515_CMD_WRITE        0x02
#define MCP2515_CMD_BIT_MODIFY   0x05
#define MCP2515_CMD_READ_STATUS  0xA0

/* ============================================================
 * MCP2515 Registers
 * ============================================================ */

#define MCP2515_CANSTAT         0x0E
#define MCP2515_CANCTRL         0x0F

#define MCP2515_TXB0CTRL        0x30
#define MCP2515_TXB0SIDH        0x31
#define MCP2515_TXB0SIDL        0x32
#define MCP2515_TXB0EID8        0x33
#define MCP2515_TXB0EID0        0x34
#define MCP2515_TXB0DLC         0x35
#define MCP2515_TXB0D0          0x36

#define MCP2515_RXB0CTRL        0x60
#define MCP2515_RXB0SIDH        0x61
#define MCP2515_RXB0SIDL        0x62
#define MCP2515_RXB0EID8        0x63
#define MCP2515_RXB0EID0        0x64
#define MCP2515_RXB0DLC         0x65
#define MCP2515_RXB0D0          0x66

#define MCP2515_CNF1            0x2A
#define MCP2515_CNF2            0x29
#define MCP2515_CNF3            0x28

#define MCP2515_CANINTE         0x2B
#define MCP2515_CANINTF         0x2C

/* ============================================================
 * MCP2515 Operating Modes
 * ============================================================ */

#define MCP2515_MODE_NORMAL     0x00
#define MCP2515_MODE_CONFIG     0x80

/* ============================================================
 * MCP2515 Status Bits
 * ============================================================ */

#define MCP2515_RX0IF           0x01
#define MCP2515_TX0REQ          0x08

/* ============================================================
 * CAN Interface State
 * ============================================================ */

static can_interface_t can_interface =
{
    0,
    -1,
    CAN_DEFAULT_BITRATE,
    0,
    0,
    0
};

/* ============================================================
 * Timestamp
 * ============================================================ */

static uint64_t get_timestamp_ns(void)
{
    struct timespec ts;

    if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0)
    {
        return 0;
    }

    return ((uint64_t)ts.tv_sec * 1000000000ULL) +
           (uint64_t)ts.tv_nsec;
}

/* ============================================================
 * CAN ID Validation
 * ============================================================ */

static int validate_can_id(uint32_t id)
{
    if (id > CAN_STANDARD_ID_MAX)
    {
        return CAN_STATUS_INVALID_PARAMETER;
    }

    return CAN_STATUS_OK;
}

/* ============================================================
 * DLC Validation
 * ============================================================ */

static int validate_dlc(uint8_t dlc)
{
    if (dlc > CAN_MAX_DATA_LENGTH)
    {
        return CAN_STATUS_INVALID_PARAMETER;
    }

    return CAN_STATUS_OK;
}

/* ============================================================
 * QNX SPI Transfer
 * ============================================================ */

static int spi_transfer(const uint8_t *tx,
                        uint8_t *rx,
                        size_t length)
{
    spi_xchng_t *xchg;
    size_t total_size;
    int status;

    if (can_interface.spi_fd < 0)
    {
        return CAN_STATUS_SPI_ERROR;
    }

    if (tx == NULL || length == 0)
    {
        return CAN_STATUS_INVALID_PARAMETER;
    }

    total_size = sizeof(spi_xchng_t) + length;

    xchg = (spi_xchng_t *)malloc(total_size);

    if (xchg == NULL)
    {
        can_interface.error_count++;
        return CAN_STATUS_SPI_ERROR;
    }

    memset(xchg, 0, total_size);

    xchg->nbytes = (uint32_t)length;

    memcpy(xchg->data, tx, length);

    status = devctl(can_interface.spi_fd,
                    DCMD_SPI_DATA_XCHNG,
                    xchg,
                    total_size,
                    NULL);

    if (status != EOK)
    {
        printf("[CAN] SPI transfer failed: %d (%s)\n",
               status,
               strerror(status));

        free(xchg);

        can_interface.error_count++;

        return CAN_STATUS_SPI_ERROR;
    }

    if (rx != NULL)
    {
        memcpy(rx,
               xchg->data,
               length);
    }

    free(xchg);

    return CAN_STATUS_OK;
}

/* ============================================================
 * SPI Configuration
 * ============================================================ */

static int spi_configure(void)
{
    spi_cfg_t cfg;
    int status;

    memset(&cfg,
           0,
           sizeof(cfg));

    /*
     * MCP2515 SPI Mode 0
     *
     * CPOL = 0
     * CPHA = 0
     */

    cfg.mode = 0;
    cfg.clock_rate = MCP2515_SPI_CLOCK;

    status = devctl(can_interface.spi_fd,
                    DCMD_SPI_SET_CONFIG,
                    &cfg,
                    sizeof(cfg),
                    NULL);

    if (status != EOK)
    {
        printf("[CAN] SPI configuration failed: %d (%s)\n",
               status,
               strerror(status));

        return CAN_STATUS_SPI_ERROR;
    }

    printf("[CAN] SPI configured: Mode 0, %u Hz\n",
           MCP2515_SPI_CLOCK);

    return CAN_STATUS_OK;
}

/* ============================================================
 * MCP2515 Register Write
 * ============================================================ */

static int mcp2515_write_register(uint8_t address,
                                  uint8_t value)
{
    uint8_t tx[3];

    tx[0] = MCP2515_CMD_WRITE;
    tx[1] = address;
    tx[2] = value;

    return spi_transfer(tx,
                        NULL,
                        sizeof(tx));
}

/* ============================================================
 * MCP2515 Multiple Register Write
 * ============================================================ */

static int mcp2515_write_registers(uint8_t address,
                                   const uint8_t *data,
                                   size_t length)
{
    uint8_t tx[32];

    if (data == NULL || length == 0)
    {
        return CAN_STATUS_INVALID_PARAMETER;
    }

    if (length > 29)
    {
        return CAN_STATUS_INVALID_PARAMETER;
    }

    tx[0] = MCP2515_CMD_WRITE;
    tx[1] = address;

    memcpy(&tx[2],
           data,
           length);

    return spi_transfer(tx,
                        NULL,
                        length + 2);
}

/* ============================================================
 * MCP2515 Register Read
 * ============================================================ */

static int mcp2515_read_register(uint8_t address,
                                 uint8_t *value)
{
    uint8_t tx[3];
    uint8_t rx[3];

    if (value == NULL)
    {
        return CAN_STATUS_INVALID_PARAMETER;
    }

    tx[0] = MCP2515_CMD_READ;
    tx[1] = address;
    tx[2] = 0x00;

    memset(rx, 0, sizeof(rx));

    if (spi_transfer(tx,
                     rx,
                     sizeof(tx)) != CAN_STATUS_OK)
    {
        return CAN_STATUS_SPI_ERROR;
    }

    *value = rx[2];

    return CAN_STATUS_OK;
}

/* ============================================================
 * MCP2515 Bit Modify
 * ============================================================ */

static int mcp2515_bit_modify(uint8_t address,
                              uint8_t mask,
                              uint8_t value)
{
    uint8_t tx[4];

    tx[0] = MCP2515_CMD_BIT_MODIFY;
    tx[1] = address;
    tx[2] = mask;
    tx[3] = value;

    return spi_transfer(tx,
                        NULL,
                        sizeof(tx));
}

/* ============================================================
 * MCP2515 Reset
 * ============================================================ */

int mcp2515_reset(void)
{
    uint8_t tx;
    uint8_t canstat;

    if (can_interface.spi_fd < 0)
    {
        return CAN_STATUS_NOT_INITIALIZED;
    }

    tx = MCP2515_CMD_RESET;

    printf("[CAN] Sending MCP2515 RESET...\n");

    if (spi_transfer(&tx,
                     NULL,
                     1) != CAN_STATUS_OK)
    {
        printf("[CAN] MCP2515 reset command failed\n");
        return CAN_STATUS_SPI_ERROR;
    }

    usleep(10000);

    printf("[CAN] MCP2515 reset command successful\n");

    /*
     * Verify MCP2515 after reset.
     *
     * CANSTAT operating mode should be
     * Configuration mode = 0x80.
     */

    if (mcp2515_read_register(MCP2515_CANSTAT,
                              &canstat) != CAN_STATUS_OK)
    {
        printf("[CAN] MCP2515 CANSTAT read failed after reset\n");

        return CAN_STATUS_SPI_ERROR;
    }

    printf("[CAN] CANSTAT after reset = 0x%02X\n",
           canstat);

    if ((canstat & 0xE0) != MCP2515_MODE_CONFIG)
    {
        printf("[CAN] MCP2515 reset verification FAILED\n");
        return CAN_STATUS_ERROR;
    }

    printf("[CAN] MCP2515 reset verification PASSED\n");

    return CAN_STATUS_OK;
}

/* ============================================================
 * MCP2515 Read Status
 * ============================================================ */

int mcp2515_read_status(uint8_t *status)
{
    uint8_t tx[2];
    uint8_t rx[2];

    if (status == NULL)
    {
        return CAN_STATUS_INVALID_PARAMETER;
    }

    if (can_interface.spi_fd < 0)
    {
        return CAN_STATUS_NOT_INITIALIZED;
    }

    tx[0] = MCP2515_CMD_READ_STATUS;
    tx[1] = 0x00;

    memset(rx, 0, sizeof(rx));

    if (spi_transfer(tx,
                     rx,
                     sizeof(tx)) != CAN_STATUS_OK)
    {
        return CAN_STATUS_SPI_ERROR;
    }

    *status = rx[1];

    return CAN_STATUS_OK;
}

/* ============================================================
 * MCP2515 Configuration
 *
 * Hardware:
 *   MCP2515 + TJA1050
 *   8 MHz oscillator
 *
 * CAN:
 *   500 kbps
 * ============================================================ */

int mcp2515_configure(uint32_t bitrate)
{
    uint8_t canstat;
    uint8_t cnf[3];

    if (can_interface.spi_fd < 0)
    {
        return CAN_STATUS_NOT_INITIALIZED;
    }

    if (bitrate != 500000U)
    {
        printf("[CAN] Unsupported bitrate: %u\n",
               (unsigned int)bitrate);

        printf("[CAN] Supported bitrate: 500000 bps\n");

        return CAN_STATUS_INVALID_PARAMETER;
    }

    /*
     * Enter configuration mode.
     */

    if (mcp2515_bit_modify(MCP2515_CANCTRL,
                           0xE0,
                           MCP2515_MODE_CONFIG)
        != CAN_STATUS_OK)
    {
        printf("[CAN] Failed to request configuration mode\n");
        return CAN_STATUS_SPI_ERROR;
    }

    usleep(1000);

    /*
     * Verify configuration mode.
     */

    if (mcp2515_read_register(MCP2515_CANSTAT,
                              &canstat)
        != CAN_STATUS_OK)
    {
        return CAN_STATUS_SPI_ERROR;
    }

    printf("[CAN] CANSTAT configuration = 0x%02X\n",
           canstat);

    if ((canstat & 0xE0) != MCP2515_MODE_CONFIG)
    {
        printf("[CAN] Failed to enter configuration mode\n");

        return CAN_STATUS_ERROR;
    }

    /*
     * 8 MHz oscillator
     * 500 kbps CAN
     *
     * CNF1 = 0x00
     * CNF2 = 0x90
     * CNF3 = 0x02
     */

    cnf[0] = 0x00;
    cnf[1] = 0x90;
    cnf[2] = 0x02;

    if (mcp2515_write_registers(MCP2515_CNF1,
                                cnf,
                                3)
        != CAN_STATUS_OK)
    {
        return CAN_STATUS_SPI_ERROR;
    }

    printf("[CAN] CNF1 = 0x%02X\n", cnf[0]);
    printf("[CAN] CNF2 = 0x%02X\n", cnf[1]);
    printf("[CAN] CNF3 = 0x%02X\n", cnf[2]);

    /*
     * RX buffer 0:
     *
     * RXM = 11
     * Accept all valid messages.
     */

    if (mcp2515_write_register(MCP2515_RXB0CTRL,
                               0x60)
        != CAN_STATUS_OK)
    {
        return CAN_STATUS_SPI_ERROR;
    }

    /*
     * Polling mode.
     * CAN interrupts disabled.
     */

    if (mcp2515_write_register(MCP2515_CANINTE,
                               0x00)
        != CAN_STATUS_OK)
    {
        return CAN_STATUS_SPI_ERROR;
    }

    /*
     * Clear CAN interrupt flags.
     */

    if (mcp2515_write_register(MCP2515_CANINTF,
                               0x00)
        != CAN_STATUS_OK)
    {
        return CAN_STATUS_SPI_ERROR;
    }

    /*
     * Return to normal mode.
     */

    if (mcp2515_bit_modify(MCP2515_CANCTRL,
                           0xE0,
                           MCP2515_MODE_NORMAL)
        != CAN_STATUS_OK)
    {
        return CAN_STATUS_SPI_ERROR;
    }

    usleep(1000);

    /*
     * Verify normal mode.
     */

    if (mcp2515_read_register(MCP2515_CANSTAT,
                              &canstat)
        != CAN_STATUS_OK)
    {
        return CAN_STATUS_SPI_ERROR;
    }

    printf("[CAN] CANSTAT normal = 0x%02X\n",
           canstat);

    if ((canstat & 0xE0) != MCP2515_MODE_NORMAL)
    {
        printf("[CAN] Failed to enter normal mode\n");

        return CAN_STATUS_ERROR;
    }

    printf("[CAN] MCP2515 configured successfully\n");
    printf("[CAN] CAN bitrate : %u bps\n",
           (unsigned int)bitrate);
    printf("[CAN] Oscillator  : 8 MHz\n");
    printf("[CAN] CAN mode    : NORMAL\n");

    return CAN_STATUS_OK;
}

/* ============================================================
 * CAN Initialization
 * ============================================================ */

int can_interface_init(void)
{
    return can_interface_init_bitrate(
        CAN_DEFAULT_BITRATE);
}

/* ============================================================
 * CAN Initialization With Bitrate
 * ============================================================ */

int can_interface_init_bitrate(uint32_t bitrate)
{
    int status;

    if (bitrate == 0)
    {
        return CAN_STATUS_INVALID_PARAMETER;
    }

    can_interface.bitrate = bitrate;

    can_interface.tx_count = 0;
    can_interface.rx_count = 0;
    can_interface.error_count = 0;

    can_interface.initialized = 0;

    /*
     * Open QNX SPI device.
     */

    can_interface.spi_fd =
        open(MCP2515_SPI_DEVICE,
             O_RDWR);

    if (can_interface.spi_fd < 0)
    {
        printf("\n");
        printf("============================================\n");
        printf(" CAN INTERFACE INITIALIZATION\n");
        printf("============================================\n");

        printf(" Controller : MCP2515\n");
        printf(" Transceiver: TJA1050\n");

        printf(" Bitrate    : %u bps\n",
               (unsigned int)bitrate);

        printf(" SPI        : FAILED\n");

        printf(" Device     : %s\n",
               MCP2515_SPI_DEVICE);

        printf(" Error      : %s\n",
               strerror(errno));

        printf("============================================\n");

        return CAN_STATUS_SPI_ERROR;
    }

    printf("\n");
    printf("============================================\n");
    printf(" CAN INTERFACE INITIALIZATION\n");
    printf("============================================\n");

    printf(" Controller : MCP2515\n");
    printf(" Transceiver: TJA1050\n");

    printf(" Bitrate    : %u bps\n",
           (unsigned int)bitrate);

    printf(" SPI Device : %s\n",
           MCP2515_SPI_DEVICE);

    printf(" SPI FD     : %d\n",
           can_interface.spi_fd);

    /*
     * Configure SPI.
     */

    status = spi_configure();

    if (status != CAN_STATUS_OK)
    {
        close(can_interface.spi_fd);
        can_interface.spi_fd = -1;

        return status;
    }

    /*
     * Reset MCP2515.
     */

    status = mcp2515_reset();

    if (status != CAN_STATUS_OK)
    {
        printf("[CAN] MCP2515 reset/verification failed\n");

        close(can_interface.spi_fd);
        can_interface.spi_fd = -1;

        return status;
    }

    /*
     * Configure MCP2515.
     */

    status = mcp2515_configure(bitrate);

    if (status != CAN_STATUS_OK)
    {
        printf("[CAN] MCP2515 configuration failed\n");

        close(can_interface.spi_fd);
        can_interface.spi_fd = -1;

        return status;
    }

    can_interface.initialized = 1;

    printf(" SPI        : CONNECTED\n");
    printf(" Controller : READY\n");
    printf(" CAN Mode   : NORMAL\n");
    printf(" Status     : HARDWARE READY\n");
    printf("============================================\n");

    return CAN_STATUS_OK;
}

/* ============================================================
 * CAN Transmission
 * ============================================================ */

int can_send_frame(const can_frame_t *frame)
{
    uint8_t tx[15];
    uint8_t txctrl;
    uint32_t wait_count;
    size_t tx_length;

    if (frame == NULL)
    {
        return CAN_STATUS_INVALID_PARAMETER;
    }

    if (!can_interface.initialized)
    {
        return CAN_STATUS_NOT_INITIALIZED;
    }

    if (validate_can_id(frame->id)
        != CAN_STATUS_OK)
    {
        return CAN_STATUS_INVALID_PARAMETER;
    }

    if (validate_dlc(frame->dlc)
        != CAN_STATUS_OK)
    {
        return CAN_STATUS_INVALID_PARAMETER;
    }

    /*
     * Wait for TX buffer 0 to become free.
     */

    for (wait_count = 0;
         wait_count < 100;
         wait_count++)
    {
        if (mcp2515_read_register(MCP2515_TXB0CTRL,
                                  &txctrl)
            != CAN_STATUS_OK)
        {
            can_interface.error_count++;
            return CAN_STATUS_TX_ERROR;
        }

        if ((txctrl & MCP2515_TX0REQ) == 0)
        {
            break;
        }

        usleep(1000);
    }

    if (wait_count >= 100)
    {
        printf("[CAN] TX buffer timeout\n");

        can_interface.error_count++;

        return CAN_STATUS_TIMEOUT;
    }

    /*
     * TX buffer format:
     *
     * SIDH
     * SIDL
     * EID8
     * EID0
     * DLC
     * DATA
     */

    tx[0] = MCP2515_CMD_WRITE;
    tx[1] = MCP2515_TXB0SIDH;

    /*
     * Standard 11-bit CAN ID.
     */

    tx[2] =
        (uint8_t)((frame->id >> 3) & 0xFF);

    tx[3] =
        (uint8_t)((frame->id & 0x07) << 5);

    tx[4] = 0x00;
    tx[5] = 0x00;

    tx[6] =
        frame->dlc & 0x0F;

    if (frame->dlc > 0)
    {
        memcpy(&tx[7],
               frame->data,
               frame->dlc);
    }

    tx_length =
        7 + frame->dlc;

    /*
     * Write TX buffer.
     */

    if (spi_transfer(tx,
                     NULL,
                     tx_length)
        != CAN_STATUS_OK)
    {
        can_interface.error_count++;

        return CAN_STATUS_TX_ERROR;
    }

    /*
     * Request transmission.
     */

    if (mcp2515_bit_modify(MCP2515_TXB0CTRL,
                           MCP2515_TX0REQ,
                           MCP2515_TX0REQ)
        != CAN_STATUS_OK)
    {
        can_interface.error_count++;

        return CAN_STATUS_TX_ERROR;
    }

    /*
     * Wait for TXREQ to clear.
     */

    for (wait_count = 0;
         wait_count < 100;
         wait_count++)
    {
        if (mcp2515_read_register(MCP2515_TXB0CTRL,
                                  &txctrl)
            != CAN_STATUS_OK)
        {
            can_interface.error_count++;

            return CAN_STATUS_TX_ERROR;
        }

        if ((txctrl & MCP2515_TX0REQ) == 0)
        {
            can_interface.tx_count++;

            printf("[CAN] TX SUCCESS "
                   "ID=0x%03X DLC=%u\n",
                   (unsigned int)frame->id,
                   (unsigned int)frame->dlc);

            return CAN_STATUS_OK;
        }

        usleep(1000);
    }

    printf("[CAN] TX timeout\n");

    can_interface.error_count++;

    return CAN_STATUS_TIMEOUT;
}

/* ============================================================
 * Send Standard CAN Message
 * ============================================================ */

int can_send_message(uint32_t id,
                     const uint8_t *data,
                     uint8_t dlc)
{
    can_frame_t frame;

    if (validate_can_id(id)
        != CAN_STATUS_OK)
    {
        return CAN_STATUS_INVALID_PARAMETER;
    }

    if (validate_dlc(dlc)
        != CAN_STATUS_OK)
    {
        return CAN_STATUS_INVALID_PARAMETER;
    }

    if (dlc > 0 && data == NULL)
    {
        return CAN_STATUS_INVALID_PARAMETER;
    }

    memset(&frame,
           0,
           sizeof(frame));

    frame.id = id;
    frame.dlc = dlc;
    frame.extended = 0;
    frame.rtr = 0;

    frame.timestamp_ns =
        get_timestamp_ns();

    if (dlc > 0)
    {
        memcpy(frame.data,
               data,
               dlc);
    }

    return can_send_frame(&frame);
}

/* ============================================================
 * RTOS Trigger Message
 * ============================================================ */

int can_send_rtos_trigger(uint8_t trigger_id)
{
    uint8_t data[2];

    data[0] = trigger_id;
    data[1] = 0x01;

    return can_send_message(
        CAN_ID_RTOS_TRIGGER,
        data,
        2);
}

/* ============================================================
 * CAN Reception
 * ============================================================ */

int can_receive_frame(can_frame_t *frame,
                      uint32_t timeout_ms)
{
    uint8_t intf = 0;

    uint8_t tx[15];
    uint8_t rx[15];

    uint8_t dlc;
    uint32_t elapsed;

    if (frame == NULL)
    {
        return CAN_STATUS_INVALID_PARAMETER;
    }

    if (!can_interface.initialized)
    {
        return CAN_STATUS_NOT_INITIALIZED;
    }

    memset(frame,
           0,
           sizeof(can_frame_t));

    /*
     * Poll CANINTF.
     */

    for (elapsed = 0;
         elapsed <= timeout_ms;
         elapsed++)
    {
        if (mcp2515_read_register(
                MCP2515_CANINTF,
                &intf)
            != CAN_STATUS_OK)
        {
            can_interface.error_count++;

            return CAN_STATUS_RX_ERROR;
        }

        if ((intf & MCP2515_RX0IF) != 0)
        {
            break;
        }

        usleep(1000);
    }

    if ((intf & MCP2515_RX0IF) == 0)
    {
        return CAN_STATUS_TIMEOUT;
    }

    /*
     * READ RX buffer 0.
     */

    memset(tx, 0, sizeof(tx));
    memset(rx, 0, sizeof(rx));

    tx[0] = MCP2515_CMD_READ;
    tx[1] = MCP2515_RXB0SIDH;

    if (spi_transfer(tx,
                     rx,
                     sizeof(rx))
        != CAN_STATUS_OK)
    {
        can_interface.error_count++;

        return CAN_STATUS_RX_ERROR;
    }

    /*
     * Decode standard 11-bit ID.
     */

    frame->id =
        ((uint32_t)rx[2] << 3) |
        ((uint32_t)(rx[3] >> 5) & 0x07);

    frame->extended = 0;

    /*
     * RTR bit.
     */

    frame->rtr =
        (rx[6] & 0x40) ? 1 : 0;

    /*
     * DLC.
     */

    dlc = rx[6] & 0x0F;

    if (dlc > CAN_MAX_DATA_LENGTH)
    {
        dlc = CAN_MAX_DATA_LENGTH;
    }

    frame->dlc = dlc;

    /*
     * Data bytes.
     */

    if (dlc > 0)
    {
        memcpy(frame->data,
               &rx[7],
               dlc);
    }

    frame->timestamp_ns =
        get_timestamp_ns();

    /*
     * Clear RX0 interrupt flag.
     */

    if (mcp2515_bit_modify(
            MCP2515_CANINTF,
            MCP2515_RX0IF,
            0x00)
        != CAN_STATUS_OK)
    {
        can_interface.error_count++;

        return CAN_STATUS_RX_ERROR;
    }

    can_interface.rx_count++;

    printf("[CAN] RX SUCCESS "
           "ID=0x%03X DLC=%u\n",
           (unsigned int)frame->id,
           (unsigned int)frame->dlc);

    return CAN_STATUS_OK;
}

/* ============================================================
 * CAN Test Message
 * ============================================================ */

int can_send_test_message(void)
{
    uint8_t test_data[8];

    test_data[0] = 0xAA;
    test_data[1] = 0x55;
    test_data[2] = 0x01;
    test_data[3] = 0x02;
    test_data[4] = 0x03;
    test_data[5] = 0x04;
    test_data[6] = 0x05;
    test_data[7] = 0x06;

    printf("[CAN] Sending test message...\n");

    printf("[CAN] ID   : 0x%03X\n",
           CAN_ID_ECU_STATUS);

    printf("[CAN] DLC  : 8\n");

    printf("[CAN] DATA : "
           "AA 55 01 02 03 04 05 06\n");

    return can_send_message(
        CAN_ID_ECU_STATUS,
        test_data,
        8);
}

/* ============================================================
 * CAN Self Test
 * ============================================================ */

int can_run_self_test(void)
{
    can_frame_t frame;
    int status;

    printf("\n");
    printf("============================================\n");
    printf(" CAN SELF TEST\n");
    printf("============================================\n");

    memset(&frame,
           0,
           sizeof(frame));

    frame.id = CAN_ID_ECU_STATUS;
    frame.dlc = 2;

    frame.data[0] = 0x55;
    frame.data[1] = 0xAA;

    frame.timestamp_ns =
        get_timestamp_ns();

    printf("[CAN] Test ID : 0x%03X\n",
           (unsigned int)frame.id);

    printf("[CAN] Test DLC: %u\n",
           (unsigned int)frame.dlc);

    printf("[CAN] Data     : %02X %02X\n",
           frame.data[0],
           frame.data[1]);

    if (!can_interface.initialized)
    {
        printf("[CAN] Result   : NOT INITIALIZED\n");

        return CAN_STATUS_NOT_INITIALIZED;
    }

    status = can_send_frame(&frame);

    if (status == CAN_STATUS_OK)
    {
        printf("[CAN] Result   : TRANSMIT SUCCESS\n");
        printf("[CAN] Hardware : MCP2515 CONNECTED\n");
    }
    else
    {
        printf("[CAN] Result   : TRANSMIT FAILED\n");
    }

    printf("============================================\n");

    return status;
}

/* ============================================================
 * Statistics
 * ============================================================ */

uint64_t can_get_tx_count(void)
{
    return can_interface.tx_count;
}

uint64_t can_get_rx_count(void)
{
    return can_interface.rx_count;
}

uint64_t can_get_error_count(void)
{
    return can_interface.error_count;
}

const can_interface_t *can_get_interface(void)
{
    return &can_interface;
}

/* ============================================================
 * CAN Status Display
 * ============================================================ */

void can_interface_print_status(void)
{
    printf("\n");
    printf("============================================\n");
    printf(" CAN INTERFACE STATUS\n");
    printf("============================================\n");

    printf("Initialized : %s\n",
           can_interface.initialized
           ? "YES"
           : "NO");

    printf("Controller  : MCP2515\n");

    printf("Transceiver : TJA1050\n");

    printf("Bitrate     : %u bps\n",
           (unsigned int)can_interface.bitrate);

    printf("SPI FD      : %d\n",
           can_interface.spi_fd);

    printf("TX Frames   : %llu\n",
           (unsigned long long)
           can_interface.tx_count);

    printf("RX Frames   : %llu\n",
           (unsigned long long)
           can_interface.rx_count);

    printf("Errors      : %llu\n",
           (unsigned long long)
           can_interface.error_count);

    if (can_interface.spi_fd >= 0 &&
        can_interface.initialized)
    {
        printf("Hardware    : CONNECTED\n");
    }
    else
    {
        printf("Hardware    : NOT CONNECTED\n");
    }

    printf("============================================\n");
}

/* ============================================================
 * CAN Shutdown
 * ============================================================ */

void can_interface_close(void)
{
    if (can_interface.spi_fd >= 0)
    {
        close(can_interface.spi_fd);

        can_interface.spi_fd = -1;
    }

    can_interface.initialized = 0;

    printf("[CAN] Interface closed\n");
}
