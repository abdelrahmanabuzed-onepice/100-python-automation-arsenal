#!/usr/bin/env python3
"""
SMTP Handshake & Deliverability Pre-Flight Inspector
===================================================
Inspects mail server health and recipient deliverability without dispatching email:
- MX record discovery and priority sorting
- Port 25/587 handshake, EHLO negotiation, STARTTLS inspection
- Pre-flight recipient verification (RCPT TO)
- Domain SPF and DMARC security policy audit

Keywords: smtp deliverability, mx checker, email verification, deliverability test, spf dmarc audit
"""

import sys
import smtplib
import socket
import json
import argparse
from typing import List, Dict, Tuple, Optional, Any

try:
    import dns.resolver
    HAS_DNSPY = True
except ImportError:
    HAS_DNSPY = False


def get_mx_hosts(domain: str) -> List[Tuple[int, str]]:
    """Retrieve and rank MX records for domain."""
    mx_records = []
    if HAS_DNSPY:
        try:
            r = dns.resolver.Resolver()
            r.nameservers = ['8.8.8.8', '1.1.1.1']
            r.timeout = 3.0
            r.lifetime = 3.0
            answers = r.resolve(domain, 'MX')
            for rdata in answers:
                mx_records.append((rdata.preference, str(rdata.exchange).rstrip('.')))
            mx_records.sort(key=lambda x: x[0])
        except Exception:
            pass
    if not mx_records:
        # Fallback to domain itself as mailhost
        mx_records.append((10, domain))
    return mx_records


def query_txt_record(name: str) -> List[str]:
    """Query TXT records using public DNS."""
    if not HAS_DNSPY:
        return []
    try:
        r = dns.resolver.Resolver()
        r.nameservers = ['8.8.8.8', '1.1.1.1']
        answers = r.resolve(name, 'TXT')
        return [str(txt.to_text()).strip('"') for txt in answers]
    except Exception:
        return []


def check_spf_dmarc(domain: str) -> Dict[str, Any]:
    """Check SPF and DMARC records for a domain."""
    records = query_txt_record(domain)
    spf = [r for r in records if r.lower().startswith("v=spf1")]

    dmarc_records = query_txt_record(f"_dmarc.{domain}")
    dmarc = [r for r in dmarc_records if r.lower().startswith("v=dmarc1")]

    return {
        "spf_found": len(spf) > 0,
        "spf_record": spf[0] if spf else None,
        "dmarc_found": len(dmarc) > 0,
        "dmarc_record": dmarc[0] if dmarc else None
    }


def probe_smtp_recipient(mx_host: str, recipient: str, sender: str = "verify@test.local",
                         port: int = 25, timeout: float = 6.0) -> Dict[str, Any]:
    """Connect to MX host, perform EHLO and test recipient acceptance."""
    info = {
        "mx_host": mx_host,
        "port": port,
        "connected": False,
        "banner": "",
        "starttls_supported": False,
        "rcpt_accepted": False,
        "smtp_code": 0,
        "response_message": ""
    }

    try:
        smtp = smtplib.SMTP(timeout=timeout)
        code, banner = smtp.connect(mx_host, port)
        info["connected"] = True
        info["banner"] = banner.decode('utf-8', errors='ignore') if isinstance(banner, bytes) else str(banner)

        # EHLO
        smtp.ehlo("tester.local")
        info["starttls_supported"] = smtp.has_extn("STARTTLS")

        # MAIL FROM
        c_mail, msg_mail = smtp.mail(sender)
        if c_mail == 250:
            c_rcpt, msg_rcpt = smtp.rcpt(recipient)
            info["smtp_code"] = c_rcpt
            info["response_message"] = msg_rcpt.decode('utf-8', errors='ignore') if isinstance(msg_rcpt, bytes) else str(msg_rcpt)
            info["rcpt_accepted"] = (c_rcpt == 250)
        else:
            info["smtp_code"] = c_mail
            info["response_message"] = msg_mail.decode('utf-8', errors='ignore') if isinstance(msg_mail, bytes) else str(msg_mail)
        
        try:
            smtp.quit()
        except Exception:
            pass

    except smtplib.SMTPConnectError as e:
        info["response_message"] = f"SMTP Connect Error: {e}"
    except socket.timeout:
        info["response_message"] = "Connection Timed Out"
    except Exception as e:
        info["response_message"] = f"Probe Error: {e}"

    return info


def verify_email_deliverability(email: str, check_mailbox: bool = False) -> Dict[str, Any]:
    """Perform comprehensive deliverability check for given email."""
    if "@" not in email:
        return {"error": "Invalid email syntax: missing '@'"}

    local_part, domain = email.strip().split("@", 1)
    domain = domain.lower()

    mx_list = get_mx_hosts(domain)
    dns_sec = check_spf_dmarc(domain)

    report = {
        "email": email,
        "domain": domain,
        "mx_hosts": mx_list,
        "security": dns_sec,
        "mailbox_check": None
    }

    if check_mailbox and mx_list:
        primary_mx = mx_list[0][1]
        probe = probe_smtp_recipient(primary_mx, email)
        report["mailbox_check"] = probe

    # Calculate deliverability readiness score
    score = 0
    if mx_list:
        score += 40
    if dns_sec["spf_found"]:
        score += 30
    if dns_sec["dmarc_found"]:
        score += 30
    report["deliverability_score"] = score

    return report


def main():
    parser = argparse.ArgumentParser(
        description="SMTP Handshake & Deliverability Pre-Flight Inspector"
    )
    parser.add_argument("email", help="Target email address or domain (e.g. user@example.com)")
    parser.add_argument("--probe-mailbox", "-p", action="store_true",
                        help="Execute live SMTP handshake and RCPT TO check on port 25")
    parser.add_argument("--json", action="store_true",
                        help="Output results as JSON")

    args = parser.parse_args()
    target = args.email if "@" in args.email else f"postmaster@{args.email}"

    data = verify_email_deliverability(target, check_mailbox=args.probe_mailbox)

    if args.json:
        print(json.dumps(data, indent=2))
        return

    print(f"\n[*] Deliverability Pre-flight for: {data['email']}")
    print(f"[*] Deliverability Health Score: {data.get('deliverability_score', 0)}/100")
    
    print("\n--- MX Host Records ---")
    if data["mx_hosts"]:
        for pref, host in data["mx_hosts"]:
            print(f"  Priority {pref:>3}: {host}")
    else:
        print("  [-] No MX records found.")

    print("\n--- Domain Email Authentication ---")
    sec = data["security"]
    print(f"  SPF Record   : {'[PASS] ' + sec['spf_record'] if sec['spf_found'] else '[FAIL] No SPF found'}")
    print(f"  DMARC Policy : {'[PASS] ' + sec['dmarc_record'] if sec['dmarc_found'] else '[FAIL] No DMARC found'}")

    if data.get("mailbox_check"):
        mb = data["mailbox_check"]
        print("\n--- Live SMTP Handshake Audit ---")
        print(f"  Target MX Host     : {mb['mx_host']}")
        print(f"  Connected          : {mb['connected']}")
        print(f"  STARTTLS Supported : {mb['starttls_supported']}")
        print(f"  Recipient Accepted : {mb['rcpt_accepted']}")
        print(f"  SMTP Response      : {mb['smtp_code']} {mb['response_message']}")


if __name__ == "__main__":
    main()
