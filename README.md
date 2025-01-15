# DNS Zone Comparison Tool

A Python script to compare DNS zones between current and new nameservers. Helps validate DNS migrations by identifying:
- Missing records
- Extra records
- TTL differences

## Installation

1. Requires Python 3.6+
2. Install dependencies:
```bash
pip install dnspython
```

## Usage

### Basic Command
```bash
python dns_compare.py <zone> <new_nameserver_ip>
```

### Arguments
- `zone`: The DNS zone to compare (e.g., example.com)
- `new_nameserver_ip`: IP address of the new nameserver to compare against

### Example
Compare example.com zone between current nameserver and new nameserver at 192.0.2.1:
```bash
python dns_compare.py example.com 192.0.2.1
```

## Output Explanation

The script outputs three types of differences:

1. **Missing Records** (❌)
   - Records present on current nameserver but missing from new nameserver
   - Format: `name record_type ttl value`

2. **Extra Records** (⚠️)
   - Records present on new nameserver but not on current nameserver
   - Format: `name record_type ttl value`

3. **TTL Differences** (⚠️)
   - Records with different TTL values between nameservers
   - Shows both old and new TTL values

If no differences are found, the script will output:
```
✅ Zones are identical!
```

## Supported Record Types
The script compares these DNS record types:
- A
- AAAA
- CNAME
- MX
- TXT
- SRV
- PTR

## Error Handling
The script will exit with an error if:
- Unable to resolve current nameserver
- Unable to query NS records from either nameserver
- Invalid zone or nameserver IP provided

## Notes
- NS records are excluded from comparison as they are expected to differ
- The script uses the system's default DNS resolver to find current nameserver
- TTL differences are shown separately from missing/extra records
