#!/usr/bin/env python3
import dns.resolver
import dns.zone
import argparse
from typing import Dict, List, Set, Tuple
import sys
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class DNSRecord:
    name: str
    record_type: str
    ttl: int
    value: str

    def __eq__(self, other):
        if not isinstance(other, DNSRecord):
            return False
        # Compare everything except TTL for equality
        return (self.name == other.name and 
                self.record_type == other.record_type and 
                self.value == other.value)

    def __hash__(self):
        # Hash everything except TTL
        return hash((self.name, self.record_type, self.value))

class DNSComparer:
    def __init__(self, zone: str, new_ns: str):
        self.zone = zone
        self.new_ns = new_ns
        # Excluding NS records from comparison as they are expected to be different
        self.record_types = ['A', 'AAAA', 'CNAME', 'MX', 'TXT', 'SRV', 'PTR']
        self.old_ns = self._get_current_nameserver()
        
    def _get_current_nameserver(self) -> str:
        """Get the first current authoritative nameserver IP for the zone"""
        try:
            # First get NS records using default resolver
            default_resolver = dns.resolver.get_default_resolver()
            ns_records = default_resolver.resolve(self.zone, 'NS')
            
            # Get the first NS record
            first_ns = str(ns_records[0])
            
            # Resolve the NS hostname to IP
            ns_ip = default_resolver.resolve(first_ns, 'A')[0]
            return str(ns_ip)
            
        except dns.exception.DNSException as e:
            print(f"Error getting current nameserver for {self.zone}: {e}")
            sys.exit(1)

    def get_resolver(self, nameserver: str) -> dns.resolver.Resolver:
        """Create a resolver instance pointing to specific nameserver"""
        resolver = dns.resolver.Resolver()
        resolver.nameservers = [nameserver]
        return resolver

    def query_records(self, nameserver: str) -> Set[DNSRecord]:
        """Query all records for a zone from specified nameserver"""
        resolver = self.get_resolver(nameserver)
        records = set()
        
        try:
            # First get NS records to verify zone exists
            ns_answer = resolver.resolve(self.zone, 'NS')
        except dns.exception.DNSException as e:
            print(f"Error querying NS records for {self.zone} from {nameserver}: {e}")
            sys.exit(1)

        for record_type in self.record_types:
            try:
                answers = resolver.resolve(self.zone, record_type)
                for rdata in answers:
                    records.add(DNSRecord(
                        name=self.zone,
                        record_type=record_type,
                        ttl=answers.ttl,
                        value=str(rdata)
                    ))
            except dns.resolver.NoAnswer:
                continue
            except dns.exception.DNSException as e:
                print(f"Warning: Error querying {record_type} records: {e}")
                continue

        return records

    def compare_zones(self) -> Tuple[Set[DNSRecord], Set[DNSRecord], Dict[str, List[Tuple[DNSRecord, DNSRecord]]]]:
        """Compare records between old and new nameservers"""
        old_records = self.query_records(self.old_ns)
        new_records = self.query_records(self.new_ns)

        # Find missing and extra records
        missing_records = old_records - new_records
        extra_records = new_records - old_records

        # Find TTL differences
        ttl_differences = defaultdict(list)
        for old_record in old_records:
            for new_record in new_records:
                if (old_record.name == new_record.name and 
                    old_record.record_type == new_record.record_type and
                    old_record.value == new_record.value and
                    old_record.ttl != new_record.ttl):
                    ttl_differences[old_record.name].append((old_record, new_record))

        return missing_records, extra_records, ttl_differences

def main():
    parser = argparse.ArgumentParser(description='Compare DNS zones between two nameservers')
    parser.add_argument('zone', help='Zone to compare (e.g., example.com)')
    parser.add_argument('new_ns', help='New nameserver IP')
    args = parser.parse_args()

    comparer = DNSComparer(args.zone, args.new_ns)
    missing_records, extra_records, ttl_differences = comparer.compare_zones()

    # Print results
    print(f"\nComparing {args.zone} between current nameserver {comparer.old_ns} and new nameserver {args.new_ns}\n")
    
    if not (missing_records or extra_records or ttl_differences):
        print("✅ Zones are identical!")
        return

    if missing_records:
        print("\n❌ Records missing from new nameserver:")
        for record in sorted(missing_records, key=lambda x: (x.name, x.record_type)):
            print(f"{record.name} {record.record_type} {record.ttl} {record.value}")

    if extra_records:
        print("\n⚠️  Extra records in new nameserver:")
        for record in sorted(extra_records, key=lambda x: (x.name, x.record_type)):
            print(f"{record.name} {record.record_type} {record.ttl} {record.value}")

    if ttl_differences:
        print("\n⚠️  TTL differences:")
        for name, differences in ttl_differences.items():
            for old_record, new_record in differences:
                print(f"{name} {old_record.record_type} {old_record.value}:")
                print(f"  Old TTL: {old_record.ttl}")
                print(f"  New TTL: {new_record.ttl}")

if __name__ == '__main__':
    main()
