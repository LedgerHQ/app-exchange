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

########################################
#        Mandatory configuration       #
########################################
# Application name
APPNAME = "Exchange"

# Application version
APPVERSION_M = 4
APPVERSION_N = 2
APPVERSION_P = 5
APPVERSION = "$(APPVERSION_M).$(APPVERSION_N).$(APPVERSION_P)"

# Application source files
APP_SOURCE_PATH += src

# Application icons following guidelines:
# https://developers.ledger.com/docs/embedded-app/design-requirements/#device-icon
ICON_NANOS = icons/nanos_app_exchange.gif
ICON_NANOX = icons/nanox_app_exchange.gif
ICON_NANOSP = icons/nanox_app_exchange.gif
ICON_STAX = icons/stax_app_exchange.gif
ICON_FLEX = icons/flex_app_exchange.gif

# Application allowed derivation curves.
# Possibles curves are: secp256k1, secp256r1, ed25519 and bls12381g1
# If your app needs it, you can specify multiple curves by using:
# `CURVE_APP_LOAD_PARAMS = <curve1> <curve2>`
CURVE_APP_LOAD_PARAMS = ed25519 secp256k1 secp256r1

# Application allowed derivation paths.
# You should request a specific path for your app.
# This serve as an isolation mechanism.
# Most application will have to request a path according to the BIP-0044
# and SLIP-0044 standards.
# If your app needs it, you can specify multiple path by using:
# `PATH_APP_LOAD_PARAMS = "44'/1'" "45'/1'"`
PATH_APP_LOAD_PARAMS = ""

# Setting to allow building variant applications
# - <VARIANT_PARAM> is the name of the parameter which should be set
#   to specify the variant that should be build.
# - <VARIANT_VALUES> a list of variant that can be build using this app code.
#   * It must at least contains one value.
#   * Values can be the app ticker or anything else but should be unique.
VARIANT_PARAM = COIN
VARIANT_VALUES = exchange

# Enabling DEBUG flag will enable PRINTF and disable optimizations
#DEBUG = 1

########################################
#     Application custom permissions   #
########################################
# See SDK `include/appflags.h` for the purpose of each permission
HAVE_APPLICATION_FLAG_DERIVE_MASTER = 1
HAVE_APPLICATION_FLAG_GLOBAL_PIN = 1
HAVE_APPLICATION_FLAG_BOLOS_SETTINGS = 1
#HAVE_APPLICATION_FLAG_LIBRARY = 1

########################################
# Application communication interfaces #
########################################
ENABLE_BLUETOOTH = 1
#ENABLE_NFC = 1

########################################
#         NBGL custom features         #
########################################
#ENABLE_NBGL_QRCODE = 1
#ENABLE_NBGL_KEYBOARD = 1
#ENABLE_NBGL_KEYPAD = 1

########################################
#          Features disablers          #
########################################
# These advanced settings allow to disable some feature that are by
# default enabled in the SDK `Makefile.standard_app`.

# DISABLE_STANDARD_APP_FILES = 1

#DISABLE_DEFAULT_IO_SEPROXY_BUFFER_SIZE = 1 # To allow custom size declaration
#DISABLE_STANDARD_APP_DEFINES = 1 # Will set all the following disablers

# Define HAVE_SPRINTF manually, don't define HAVE_SNPRINTF_FORMAT_U
DISABLE_STANDARD_SNPRINTF = 1
DEFINES += HAVE_SPRINTF

# Save some flash size
ifeq ($(TARGET_NAME),TARGET_NANOS)
DISABLE_STANDARD_WEBUSB = 1
endif

#DISABLE_STANDARD_USB = 1
#DISABLE_STANDARD_BAGL_UX_FLOW = 1
#DISABLE_DEBUG_LEDGER_ASSERT = 1
#DISABLE_DEBUG_THROW = 1

########################################
#            Testing flags             #
########################################

# /!\
# If you are a Ledger user, do NOT modify this in ANY case
# /!\

ifdef TESTING
    $(warning [WARNING] TESTING enabled)
    DEFINES += TESTING
    TEST_BUILD = 1
endif

ifdef TEST_PUBLIC_KEY
    $(warning [WARNING] TEST_PUBLIC_KEY enabled)
    DEFINES += TEST_PUBLIC_KEY
    TEST_BUILD = 1
endif

ifdef BYPASS_TRANSACTION_ID_CHECK
    $(warning [WARNING] BYPASS_TRANSACTION_ID_CHECK enabled)
    DEFINES += BYPASS_TRANSACTION_ID_CHECK
    TEST_BUILD = 1
endif

ifdef BYPASS_CHECK_ADDRESS
    $(warning [WARNING] BYPASS_CHECK_ADDRESS enabled)
    DEFINES += BYPASS_CHECK_ADDRESS
    TEST_BUILD = 1
endif

ifdef TRUSTED_NAME_TEST_KEY
    $(info [INFO] TRUSTED_NAME_TEST_KEY enabled)
    DEFINES += TRUSTED_NAME_TEST_KEY
endif

ifdef FIXED_TLV_CHALLENGE
    $(info [INFO] FIXED_TLV_CHALLENGE enabled)
    DEFINES += FIXED_TLV_CHALLENGE
endif

ifeq ($(TEST_BUILD),1)
    $(warning [WARNING] TEST_BUILD enabled)
	APPNAME = "Exchange TEST"
	VARIANT_VALUES = "exchangetest"
	DEFINES += TEST_BUILD
endif

########################################
#      Protobuf files regeneration     #
########################################
.PHONY: proto
proto:
	make -C ledger-nanopb/generator/proto
	protoc --nanopb_out=. src/proto/protocol.proto --plugin=protoc-gen-nanopb=ledger-nanopb/generator/protoc-gen-nanopb
	protoc --python_out=. src/proto/protocol.proto
	mv src/proto/protocol_pb2.py client/src/ledger_app_clients/exchange/pb/exchange_pb2.py

########################################

include $(BOLOS_SDK)/Makefile.standard_app
