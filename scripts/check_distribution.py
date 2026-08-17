"""Check location distribution in cleaned jobs"""

import json
from collections import Counter

with open("data/json/jobs_cleaned.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"\n📊 Total Jobs: {len(data)}")
print("=" * 60)

# Country distribution
countries = [j["location_country"] for j in data]
country_counts = Counter(countries)

print("\n🌍 COUNTRY DISTRIBUTION:")
print("-" * 60)
for country, count in sorted(country_counts.items(), key=lambda x: -x[1]):
    percentage = count / len(data) * 100
    print(f"{country:20s}: {count:4d} jobs ({percentage:5.1f}%)")

# City distribution (top 20)
cities = [j["location_city"] for j in data]
city_counts = Counter(cities)

print("\n🏙️  TOP 20 CITIES:")
print("-" * 60)
for city, count in sorted(city_counts.items(), key=lambda x: -x[1])[:20]:
    percentage = count / len(data) * 100
    print(f"{city:20s}: {count:4d} jobs ({percentage:5.1f}%)")

# Remote type distribution
remote_types = [j["remote_type"] for j in data]
remote_counts = Counter(remote_types)

print("\n💼 REMOTE TYPE DISTRIBUTION:")
print("-" * 60)
for rtype, count in sorted(remote_counts.items(), key=lambda x: -x[1]):
    percentage = count / len(data) * 100
    print(f"{rtype:20s}: {count:4d} jobs ({percentage:5.1f}%)")

# Employment type distribution
emp_types = [j["employment_type"] for j in data]
emp_counts = Counter(emp_types)

print("\n📋 EMPLOYMENT TYPE DISTRIBUTION:")
print("-" * 60)
for etype, count in sorted(emp_counts.items(), key=lambda x: -x[1]):
    percentage = count / len(data) * 100
    print(f"{etype:20s}: {count:4d} jobs ({percentage:5.1f}%)")

print("\n" + "=" * 60)
