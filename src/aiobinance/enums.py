# enums.py
# aiobinance
#
# Created by David on 04/11/2024.
# Copyright © 2024 David. All rights reserved.

from enum import Enum, Flag, auto


class FiatTransactionType(Enum):
    DEPOSIT = "0"
    WITHDRAW = "1"


class FiatStatus(Enum):
    PROCESSING = "Processing"
    FAILED = "Failed"
    SUCCESSFUL = "Successful"
    FINISHED = "Finished"
    REFUNDING = "Refunding"
    REFUNDED = "Refunded"
    REFUND_FAILED = "Refund Failed"
    ORDER_PARTIAL_CREDIT_STOPPED = "Order Partial Credit Stopped"


class EndpointSecurity(Flag):
    NONE = auto()
    TRADE = auto()
    USER_DATA = auto()
    USER_STREAM = auto()
    SIGNED = TRADE | USER_DATA


class SymbolStatus(Enum):
    PRE_TRADING = "PRE_TRADING"
    TRADING = "TRADING"
    POST_TRADING = "POST_TRADING"
    END_OF_DAY = "END_OF_DAY"
    HALT = "HALT"
    AUCTION_MATCH = "AUCTION_MATCH"
    BREAK = "BREAK"


class AccountSymbolPermissions(Enum):
    SPOT = "SPOT"
    MARGIN = "MARGIN"
    LEVERAGED = "LEVERAGED"
    TRD_GRP_002 = "TRD_GRP_002"
    TRD_GRP_003 = "TRD_GRP_003"
    TRD_GRP_004 = "TRD_GRP_004"
    TRD_GRP_005 = "TRD_GRP_005"
    TRD_GRP_006 = "TRD_GRP_006"
    TRD_GRP_007 = "TRD_GRP_007"
    TRD_GRP_008 = "TRD_GRP_008"
    TRD_GRP_009 = "TRD_GRP_009"
    TRD_GRP_010 = "TRD_GRP_010"
    TRD_GRP_011 = "TRD_GRP_011"
    TRD_GRP_012 = "TRD_GRP_012"
    TRD_GRP_013 = "TRD_GRP_013"
    TRD_GRP_014 = "TRD_GRP_014"
    TRD_GRP_015 = "TRD_GRP_015"
    TRD_GRP_016 = "TRD_GRP_016"
    TRD_GRP_017 = "TRD_GRP_017"
    TRD_GRP_018 = "TRD_GRP_018"
    TRD_GRP_019 = "TRD_GRP_019"
    TRD_GRP_020 = "TRD_GRP_020"
    TRD_GRP_021 = "TRD_GRP_021"
    TRD_GRP_022 = "TRD_GRP_022"
    TRD_GRP_023 = "TRD_GRP_023"
    TRD_GRP_024 = "TRD_GRP_024"
    TRD_GRP_025 = "TRD_GRP_025"
