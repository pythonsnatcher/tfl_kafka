import requests

# Severity mapping for TfL Tube statuses
status_severity = {
    "Suspended": 1,
    "Severe Delays": 2,
    "Part Suspended": 3,
    "Planned Closure": 4,
    "Minor Delays": 5,
    "Good Service": 6
}

def fetch_tube_status():
    url = "https://api.tfl.gov.uk/Line/Mode/tube/Status"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    tube_statuses = []
    for line in data:
        line_id = line.get('id')
        name = line.get('name')
        statuses = line.get('lineStatuses', [])
        if statuses:
            status_desc = statuses[0].get('statusSeverityDescription', 'Unknown')
        else:
            status_desc = 'Unknown'
        severity = status_severity.get(status_desc, -1)  # use -1 if unknown
        tube_statuses.append({
            'line_id': line_id,
            'name': name,
            'status': status_desc,
            'severity': severity
        })
    return tube_statuses

if __name__ == "__main__":
    statuses = fetch_tube_status()
    for status in statuses:
        print(f"{status['name']} : {status['status']} {status['severity']}")
