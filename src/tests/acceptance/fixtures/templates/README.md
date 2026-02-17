# Test Template Fixtures

This directory contains template fixtures for acceptance tests.

## Templates

| Template ID | Format | Purpose |
|-------------|--------|---------|
| skeleton-template.docx | Word | Walking skeleton - minimal template |
| airport-transfer-v2.docx | Word | Airport transfer vouchers |
| sightseeing-tour-v1.odt | LibreOffice | Sightseeing tour vouchers |

## Creating Test Templates

For acceptance tests, create minimal templates with the required placeholders:

### skeleton-template.docx
```
Voucher for: {{customer.last_name}}
```

### airport-transfer-v2.docx
```
Airport Transfer Voucher

Customer: {{customer.title}} {{customer.first_name}} {{customer.last_name}}
Email: {{customer.email}}

Service: {{service.name}}
Provider: {{service.provider}}
Pickup: {{service.pickup_time}} at {{service.pickup_location}}
Dropoff: {{service.dropoff_location}}
Passengers: {{service.passengers}}
Confirmation: {{service.confirmation_code}}
```

### sightseeing-tour-v1.odt
```
Sightseeing Tour Voucher

Guest: {{customer.title}} {{customer.first_name}} {{customer.last_name}}

Tour: {{service.name}}
Provider: {{service.provider}}
Date: {{service.tour_date}}
Time: {{service.tour_time}}
Meeting Point: {{service.meeting_point}}
Duration: {{service.duration}}
Confirmation: {{service.confirmation_code}}
```

## Note

In the test infrastructure, templates are mocked in memory for speed.
These physical template files are used for integration tests that
exercise the real filesystem adapter.
