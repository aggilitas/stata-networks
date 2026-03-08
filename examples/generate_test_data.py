"""
Test Data Generator for Networks ADO Package
Generates sample datasets for testing network_calc command
"""

import pandas as pd
import numpy as np

test_provinces = ['ankara', 'istanbul', 'izmir', 'kars', 'adana']
years = [2018, 2019, 2020]
features = ['ankara', 'istanbul', 'izmir', 'kars', 'adana']

np.random.seed(42)

def generate_interaction_data():
    """
    Generate interaction network test data (multi-subnet)
    source_value = N_i^X, constant per (year, feature, source)
    target_value = N_j^X, constant per (year, feature, target)
    """
    data = []
    for year in years:
        node_values = {}
        for feature in features:
            for node in test_provinces:
                node_values[(year, feature, node)] = np.random.randint(1000, 50000)
        for feature in features:
            for source in test_provinces:
                for target in test_provinces:
                    if source != target:
                        data.append({
                            'year': year,
                            'feature': feature,
                            'source': source,
                            'target': target,
                            'source_value': node_values[(year, feature, source)],
                            'target_value': node_values[(year, feature, target)],
                        })
    df = pd.DataFrame(data)
    check = df.groupby(['year', 'feature', 'source'])['source_value'].nunique()
    assert (check == 1).all(), "source_value not constant per (year, feature, source)!"
    print(f"Interaction: {len(df)} rows, consistency OK")
    return df

def generate_flow_multi_data():
    data = []
    for year in years:
        for feature in features:
            for source in test_provinces:
                for target in test_provinces:
                    if source != target:
                        flow_value = np.random.randint(100, 5000)
                        data.append({
                            'year': year, 'feature': feature,
                            'source': source, 'target': target,
                            'source_value': flow_value, 'target_value': flow_value,
                        })
    df = pd.DataFrame(data)
    print(f"Flow Multi: {len(df)} rows")
    return df

def generate_flow_single_data():
    data = []
    for year in years:
        for source in test_provinces:
            for target in test_provinces:
                if source != target:
                    flow_value = np.random.randint(500, 20000)
                    data.append({
                        'year': year, 'source': source, 'target': target,
                        'source_value': flow_value, 'target_value': flow_value,
                    })
    df = pd.DataFrame(data)
    print(f"Flow Single: {len(df)} rows")
    return df

def generate_attribute_single_data():
    data = []
    for year in years:
        node_attr = {n: np.random.uniform(10000, 50000) for n in test_provinces}
        for source in test_provinces:
            for target in test_provinces:
                if source != target:
                    data.append({
                        'year': year, 'source': source, 'target': target,
                        'source_value': node_attr[source], 'target_value': node_attr[target],
                    })
    df = pd.DataFrame(data)
    print(f"Attribute Single: {len(df)} rows")
    return df

def generate_attribute_multi_data():
    sectors = ['agriculture', 'manufacturing', 'services']
    data = []
    for year in years:
        for sector in sectors:
            node_attr = {n: np.random.uniform(1000, 10000) for n in test_provinces}
            for source in test_provinces:
                for target in test_provinces:
                    if source != target:
                        data.append({
                            'year': year, 'feature': sector,
                            'source': source, 'target': target,
                            'source_value': node_attr[source], 'target_value': node_attr[target],
                        })
    df = pd.DataFrame(data)
    print(f"Attribute Multi: {len(df)} rows")
    return df

if __name__ == "__main__":
    generate_interaction_data().to_csv('test_interaction_multi.csv', index=False)
    generate_flow_multi_data().to_csv('test_flow_multi.csv', index=False)
    generate_flow_single_data().to_csv('test_flow_single.csv', index=False)
    generate_attribute_single_data().to_csv('test_attribute_single.csv', index=False)
    generate_attribute_multi_data().to_csv('test_attribute_multi.csv', index=False)
    print("Done.")
