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

APP_LOAD_PARAMS= --curve ed25519 --path "44'/1234'" --appFlags 0x240 $(COMMON_LOAD_PARAMS)

APPVERSION_M=1
APPVERSION_N=0
APPVERSION_P=0
APPVERSION=$(APPVERSION_M).$(APPVERSION_N).$(APPVERSION_P)
APPNAME = "Boilerplate"

DEFINES += $(DEFINES_LIB)


ifeq ($(TARGET_NAME),TARGET_NANOX)
	ICONNAME=icons/nanox_app_boilerplate.gif
else
	ICONNAME=icons/nanos_app_boilerplate.gif
endif


################
# Default rule #
################
all: default

############
# Platform #
############

DEFINES   += OS_IO_SEPROXYHAL
DEFINES   += HAVE_BAGL HAVE_SPRINTF
DEFINES   += HAVE_IO_USB HAVE_L4_USBLIB IO_USB_MAX_ENDPOINTS=6 IO_HID_EP_LENGTH=64 HAVE_USB_APDU
DEFINES   += LEDGER_MAJOR_VERSION=$(APPVERSION_M) LEDGER_MINOR_VERSION=$(APPVERSION_N) LEDGER_PATCH_VERSION=$(APPVERSION_P)

# U2F
DEFINES   += HAVE_U2F HAVE_IO_U2F
DEFINES   += U2F_PROXY_MAGIC=\"BOIL\"
DEFINES   += USB_SEGMENT_SIZE=64
DEFINES   += BLE_SEGMENT_SIZE=32 #max MTU, min 20

WEBUSB_URL     = www.ledgerwallet.com
DEFINES       += HAVE_WEBUSB WEBUSB_URL_SIZE_B=$(shell echo -n $(WEBUSB_URL) | wc -c) WEBUSB_URL=$(shell echo -n $(WEBUSB_URL) | sed -e "s/./\\\'\0\\\',/g")

DEFINES   += UNUSED\(x\)=\(void\)x
DEFINES   += APPVERSION=\"$(APPVERSION)\"


ifeq ($(TARGET_NAME),TARGET_NANOX)
DEFINES   	  += IO_SEPROXYHAL_BUFFER_SIZE_B=300
DEFINES       += HAVE_BLE BLE_COMMAND_TIMEOUT_MS=2000
DEFINES       += HAVE_BLE_APDU # basic ledger apdu transport over BLE

DEFINES       += HAVE_GLO096
DEFINES       += HAVE_BAGL BAGL_WIDTH=128 BAGL_HEIGHT=64
DEFINES       += HAVE_BAGL_ELLIPSIS # long label truncation feature
DEFINES       += HAVE_BAGL_FONT_OPEN_SANS_REGULAR_11PX
DEFINES       += HAVE_BAGL_FONT_OPEN_SANS_EXTRABOLD_11PX
DEFINES       += HAVE_BAGL_FONT_OPEN_SANS_LIGHT_16PX
DEFINES		  += HAVE_UX_FLOW
else
DEFINES   	  += IO_SEPROXYHAL_BUFFER_SIZE_B=128
endif

# Enabling debug PRINTF
DEBUG = 1
ifneq ($(DEBUG),0)

        ifeq ($(TARGET_NAME),TARGET_NANOX)
                DEFINES   += HAVE_PRINTF PRINTF=mcu_usb_printf
        else
                DEFINES   += HAVE_PRINTF PRINTF=screen_printf
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
LDLIBS   += -lm -lgcc -lc

# import rules to compile glyphs(/pone)
include $(BOLOS_SDK)/Makefile.glyphs

### variables processed by the common makefile.rules of the SDK to grab source files and include dirs
APP_SOURCE_PATH  += src
SDK_SOURCE_PATH  += lib_stusb lib_stusb_impl lib_u2f

ifeq ($(TARGET_NAME),TARGET_NANOX)
SDK_SOURCE_PATH  += lib_blewbxx lib_blewbxx_impl
SDK_SOURCE_PATH  += lib_ux
endif

load: all
	python -m ledgerblue.loadApp $(APP_LOAD_PARAMS)

load-offline: all
	python -m ledgerblue.loadApp $(APP_LOAD_PARAMS) --offline

delete:
	python -m ledgerblue.deleteApp $(COMMON_DELETE_PARAMS)

release: all
	export APP_LOAD_PARAMS_EVALUATED="$(shell printf '\\"%s\\" ' $(APP_LOAD_PARAMS))"; \
	cat load-template.sh | envsubst > load.sh
	chmod +x load.sh
	tar -zcf boilerplate-ledger-app-$(APPVERSION).tar.gz load.sh bin/app.hex
	rm load.sh

# import generic rules from the sdk
include $(BOLOS_SDK)/Makefile.rules

#add dependency on custom makefile filename
dep/%.d: %.c Makefile



listvariants:
	@echo VARIANTS COIN boilerplate
