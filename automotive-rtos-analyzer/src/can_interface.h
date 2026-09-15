#ifndef CAN_INTERFACE_H
#define CAN_INTERFACE_H

/*
 * Automotive RTOS Performance & Latency Analyzer
 *
 * CAN Interface
 * Controller : MCP2515
 * Transceiver: TJA1050
 *
 * Step 12 - CAN Interface
 */

#include <stdint.h>
#include <stddef.h>

/* ============================================================
 * CAN Configuration
 * ============================================================ */

#define CAN_MAX_DATA_LENGTH      8
#define CAN_DEFAULT_BITRATE      500000U

/* Standard CAN ID range: 0x000 - 0x7FF */
#define CAN_STANDARD_ID_MAX      0x7FFU

/* Example CAN message IDs */
#define CAN_ID_ECU_STATUS        0x100U
#define CAN_ID_ECU_COMMAND       0x101U
#define CAN_ID_RTOS_TRIGGER      0x200U
#define CAN_ID_RTOS_RESPONSE     0x201U


/* ============================================================
 * CAN Frame Structure
 * ============================================================ */

typedef struct
{
    uint32_t id;

    uint8_t dlc;

    uint8_t data[CAN_MAX_DATA_LENGTH];

    uint8_t extended;

    uint8_t rtr;

    uint64_t timestamp_ns;

} can_frame_t;


/* ============================================================
 * CAN Status
 * ============================================================ */

typedef enum
{
    CAN_STATUS_OK = 0,

    CAN_STATUS_ERROR = -1,

    CAN_STATUS_NOT_INITIALIZED = -2,

    CAN_STATUS_INVALID_PARAMETER = -3,

    CAN_STATUS_TX_ERROR = -4,

    CAN_STATUS_RX_ERROR = -5,

    CAN_STATUS_SPI_ERROR = -6,

    CAN_STATUS_TIMEOUT = -7

} can_status_t;


/* ============================================================
 * CAN Interface State
 * ============================================================ */

typedef struct
{
    int initialized;

    int spi_fd;

    uint32_t bitrate;

    uint64_t tx_count;

    uint64_t rx_count;

    uint64_t error_count;

} can_interface_t;


/* ============================================================
 * Initialization
 * ============================================================ */

/*
 * Initialize CAN interface.
 *
 * Returns:
 *   CAN_STATUS_OK on success
 *   Negative error code on failure
 */
int can_interface_init(void);


/*
 * Initialize CAN interface with selected bitrate.
 *
 * Example:
 *   can_interface_init_bitrate(500000);
 */
int can_interface_init_bitrate(uint32_t bitrate);


/* ============================================================
 * CAN Transmission
 * ============================================================ */

/*
 * Send a CAN frame.
 */
int can_send_frame(const can_frame_t *frame);


/*
 * Send a standard CAN message.
 */
int can_send_message(uint32_t id,
                     const uint8_t *data,
                     uint8_t dlc);


/*
 * Send an RTOS trigger message.
 *
 * Used to generate an external ECU event
 * that can trigger an RTOS workload.
 */
int can_send_rtos_trigger(uint8_t trigger_id);


/* ============================================================
 * CAN Reception
 * ============================================================ */

/*
 * Receive a CAN frame.
 *
 * timeout_ms:
 *   Timeout in milliseconds.
 */
int can_receive_frame(can_frame_t *frame,
                       uint32_t timeout_ms);


/* ============================================================
 * CAN Testing
 * ============================================================ */

/*
 * Send a test CAN frame.
 *
 * This is useful for verifying the CAN interface.
 */
int can_send_test_message(void);


/*
 * Run CAN interface self-test.
 */
int can_run_self_test(void);


/* ============================================================
 * MCP2515 Functions
 * ============================================================ */

/*
 * Reset MCP2515 controller.
 */
int mcp2515_reset(void);


/*
 * Configure MCP2515 controller.
 */
int mcp2515_configure(uint32_t bitrate);


/*
 * Read MCP2515 status.
 */
int mcp2515_read_status(uint8_t *status);


/* ============================================================
 * Statistics
 * ============================================================ */

/*
 * Get number of transmitted CAN frames.
 */
uint64_t can_get_tx_count(void);


/*
 * Get number of received CAN frames.
 */
uint64_t can_get_rx_count(void);


/*
 * Get number of CAN errors.
 */
uint64_t can_get_error_count(void);


/*
 * Get current CAN interface state.
 */
const can_interface_t *can_get_interface(void);


/* ============================================================
 * Shutdown
 * ============================================================ */

/*
 * Close CAN interface.
 */
void can_interface_close(void);


/*
 * Print CAN interface status.
 */
void can_interface_print_status(void);

#endif /* CAN_INTERFACE_H */
