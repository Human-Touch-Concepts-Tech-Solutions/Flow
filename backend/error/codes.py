from enum import Enum



class ErrorClassification(Enum):
    #=========================================================================
    # 1xxx: Arguments and Request Structures
    #=========================================================================
    MISSING_ARGUMENT = ("1001", "Required runtime parameters or arguments were missing or blank.")
    MALFORMED_PAYLOAD = ("1002", "The data structure format is unexpected or corrupt.")

    #=========================================================================
    # 2xxx: Credentials and Restrictions
    #=========================================================================
    CREDENTIALS_MISSING = ("2001", "Target system authentication tokens or env variables are unassigned.")
    PRIVILEGE_DENIED = ("2002", "Security signature check failed: Insufficient operation rights.")
    SECURITY_ISOLATION_BLOCK = ("2003", "Request blocked: Target domain or address points to a private or restricted interface.")

    #=========================================================================
    # 3xxx: External System and Network Issues / Direct Connection Disruptions
    #=========================================================================
    TIMEOUT_EXCEEDED = ("3001", "The downstream server network socket took too long to respond.")
    BAD_GATEWAY_RESPONSE = ("3002", "External provider responded with a non-200 failure status code.")

    #=========================================================================
    # 4xxx: Process Failure Exhaustion
    #=========================================================================
    ORCHESTRATION_EXHAUSTED = ("4001", "All recovery paths, retries, and fallbacks failed completely.")
    PROVIDER_QUOTA_DEPLETED = ("4002", "All underlying provider accounts, keys, and retry fallbacks are maxed out.")

    @property
    def code_id(self) -> str:
        ######################################################################
        # Dynamically extracts the first element of the value tuple (e.g., '1001')
        ######################################################################
        return self.value[0]

    @property
    def default_message(self) -> str:
        ######################################################################
        # Dynamically extracts the second element of the value tuple
        ######################################################################
        return self.value[1]