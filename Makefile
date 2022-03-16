#*******************************************************************************
#   Ledger App
#   (c) 2017 Ledger
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#*******************************************************************************

ifeq ($(BOLOS_SDK),)
$(error Environment variable BOLOS_SDK is not set)
endif
include $(BOLOS_SDK)/Makefile.defines

APP_LOAD_PARAMS= --curve ed25519 --curve secp256k1 --curve secp256r1 --path "" --appFlags 0x240 $(COMMON_LOAD_PARAMS)

APPVERSION_M=2
APPVERSION_N=0
APPVERSION_P=8
APPVERSION=$(APPVERSION_M).$(APPVERSION_N).$(APPVERSION_P)-baanx-test
APPNAME = "Exchange"

DEFINES += $(DEFINES_LIB)

TESTING=1
TEST_PUBLIC_KEY=1

ifdef TESTING
    $(info [INFO] TESTING enabled)
    DEFINES += TESTING
endif

ifdef TEST_PUBLIC_KEY
    $(info [INFO] TEST_PUBLIC_KEY enabled)
    DEFINES += TEST_PUBLIC_KEY
endif

ifeq ($(TARGET_NAME),TARGET_NANOS)
	ICONNAME=icons/nanos_app_exchange.gif
else
	ICONNAME=icons/nanox_app_exchange.gif
endif

PROTO_C_FILE = src/proto/protocol.pb.c

################
# Default rule #
################
all: $(PROTO_C_FILE) default

############
# Platform #
############

DEFINES   += OS_IO_SEPROXYHAL
DEFINES   += HAVE_BAGL HAVE_SPRINTF
DEFINES   += HAVE_IO_USB HAVE_L4_USBLIB IO_USB_MAX_ENDPOINTS=4 IO_HID_EP_LENGTH=64 HAVE_USB_APDU
DEFINES   += LEDGER_MAJOR_VERSION=$(APPVERSION_M) LEDGER_MINOR_VERSION=$(APPVERSION_N) LEDGER_PATCH_VERSION=$(APPVERSION_P)

DEFINES   += USB_SEGMENT_SIZE=64
DEFINES   += BLE_SEGMENT_SIZE=32 #max MTU, min 20

DEFINES   += UNUSED\(x\)=\(void\)x
DEFINES   += APPVERSION=\"$(APPVERSION)\"

ifeq ($(TARGET_NAME),TARGET_NANOX)
DEFINES       += HAVE_BLE BLE_COMMAND_TIMEOUT_MS=2000
DEFINES       += HAVE_BLE_APDU # basic ledger apdu transport over BLE
endif

ifeq ($(TARGET_NAME),TARGET_NANOS)
DEFINES       += IO_SEPROXYHAL_BUFFER_SIZE_B=128
else
DEFINES       += IO_SEPROXYHAL_BUFFER_SIZE_B=300
DEFINES       += HAVE_GLO096
DEFINES       += HAVE_BAGL BAGL_WIDTH=128 BAGL_HEIGHT=64
DEFINES       += HAVE_BAGL_ELLIPSIS # long label truncation feature
DEFINES       += HAVE_BAGL_FONT_OPEN_SANS_REGULAR_11PX
DEFINES       += HAVE_BAGL_FONT_OPEN_SANS_EXTRABOLD_11PX
DEFINES       += HAVE_BAGL_FONT_OPEN_SANS_LIGHT_16PX
endif

DEFINES       += HAVE_UX_FLOW
DEFINES       += HAVE_STACK_OVERFLOW_CHECK
# Enabling debug PRINTF

ifndef DEBUG
        DEBUG = 0
endif

ifneq ($(DEBUG),0)
        DEFINES   += HAVE_STACK_OVERFLOW_CHECK
        ifeq ($(TARGET_NAME),TARGET_NANOS)
                DEFINES   += HAVE_PRINTF PRINTF=screen_printf
        else
                DEFINES   += HAVE_PRINTF PRINTF=mcu_usb_printf
        endif
else
        DEFINES   += PRINTF\(...\)=
endif

##############
#  Compiler  #
##############
ifneq ($(BOLOS_ENV),)
$(info BOLOS_ENV=$(BOLOS_ENV))
CLANGPATH := $(BOLOS_ENV)/clang-arm-fropi/bin/
GCCPATH := $(BOLOS_ENV)/gcc-arm-none-eabi-5_3-2016q1/bin/
else
$(info BOLOS_ENV is not set: falling back to CLANGPATH and GCCPATH)
endif
ifeq ($(CLANGPATH),)
$(info CLANGPATH is not set: clang will be used from PATH)
endif
ifeq ($(GCCPATH),)
$(info GCCPATH is not set: arm-none-eabi-* will be used from PATH)
endif

CC       := $(CLANGPATH)clang

#CFLAGS   += -O0
CFLAGS   += -O3 -Os

AS     := $(GCCPATH)arm-none-eabi-gcc

LD       := $(GCCPATH)arm-none-eabi-gcc
LDFLAGS  += -O3 -Os
#LDFLAGS  += -O0
LDLIBS   += -lm -lgcc -lc

# import rules to compile glyphs(/pone)
include $(BOLOS_SDK)/Makefile.glyphs

### variables processed by the common makefile.rules of the SDK to grab source files and include dirs
APP_SOURCE_PATH  += src
SDK_SOURCE_PATH  += lib_stusb lib_stusb_impl
SDK_SOURCE_PATH  += lib_ux

ifeq ($(TARGET_NAME),TARGET_NANOX)
SDK_SOURCE_PATH  += lib_blewbxx lib_blewbxx_impl
endif

PROTO_FILE = src/proto/protocol.proto

# This will generate both the .pb.c and the .pb.h files
$(PROTO_C_FILE): $(PROTO_FILE)
	protoc --nanopb_out=. $(PROTO_FILE) --plugin=protoc-gen-nanopb=ledger-nanopb/generator/protoc-gen-nanopb


load: all
	python3 -m ledgerblue.loadApp $(APP_LOAD_PARAMS)

load-offline: all
	python3 -m ledgerblue.loadApp $(APP_LOAD_PARAMS) --offline

delete:
	python3 -m ledgerblue.deleteApp $(COMMON_DELETE_PARAMS)

release: all
	export APP_LOAD_PARAMS_EVALUATED="$(shell printf '\\"%s\\" ' $(APP_LOAD_PARAMS))"; \
	cat load-template.sh | envsubst > load.sh
	chmod +x load.sh
	tar -zcf app-exchange-$(APPVERSION).tar.gz load.sh bin/app.hex
	rm load.sh

# import generic rules from the sdk
include $(BOLOS_SDK)/Makefile.rules

#add dependency on custom makefile filename
dep/%.d: %.c Makefile



listvariants:
	@echo VARIANTS COIN exchange
