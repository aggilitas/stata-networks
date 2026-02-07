"""
Test Data Generator for Networks ADO Package
Generates sample datasets for testing network_calc command
"""

import pandas as pd
import numpy as np
import itertools

# Test parameters
test_provinces = ['ankara', 'istanbul', 'izmir', 'kars', 'adana']
years = [2018, 2019, 2020]
features = ['ankara', 'istanbul', 'izmir', 'kars', 'adana']  # Birth places

np.random.seed(42)

def generate_interaction_data():
    """
    Generate interaction network test data (multi-subnet)
    Format: year feature source target source_value target_value
    """
    data = []
    
    for year in years:
        for feature in features:
            for source in test_provinces:
                for target in test_provinces:
                    if source != target:  # No self-loops
                        # Simulate population born in 'feature' living in source
                        source_value = np.random.randint(1000, 50000)
                        # Simulate population born in 'feature' living in target
                        target_value = np.random.randint(1000, 50000)
                        
                        data.append({
                            'year': year,
                            'feature': feature,
                            'source': source,
                            'target': target,
                            'source_value': source_value,
                            'target_value': target_value
                        })
    
    df = pd.DataFrame(data)
    print(f"\nInteraction Network Data:")
    print(f"  Rows: {len(df)}")
    print(f"  Columns: {df.columns.tolist()}")
    print(f"\nSample (first 10 rows):")
    print(df.head(10))
    
    return df

def generate_flow_multi_data():
    """
    Generate flow network test data (multi-subnet)
    Format: year feature source target source_value target_value
    """
    data = []
    
    for year in years:
        for feature in features:
            for source in test_provinces:
                for target in test_provinces:
                    if source != target:
                        # Migration flow from source to target (feature-based)
                        flow_value = np.random.randint(100, 5000)
                        # For flow, we use same value for both (bidirectional data)
                        data.append({
                            'year': year,
                            'feature': feature,
                            'source': source,
                            'target': target,
                            'source_value': flow_value,
                            'target_value': flow_value  # Same value for consistency
                        })
    
    df = pd.DataFrame(data)
    print(f"\nFlow Network Multi Data:")
    print(f"  Rows: {len(df)}")
    print(f"  Columns: {df.columns.tolist()}")
    print(f"\nSample (first 10 rows):")
    print(df.head(10))
    
    return df

def generate_flow_single_data():
    """
    Generate flow network test data (single-subnet)
    Format: year source target source_value target_value
    """
    data = []
    
    for year in years:
        for source in test_provinces:
            for target in test_provinces:
                if source != target:
                    # Total migration flow
                    flow_value = np.random.randint(500, 20000)
                    data.append({
                        'year': year,
                        'source': source,
                        'target': target,
                        'source_value': flow_value,
                        'target_value': flow_value
                    })
    
    df = pd.DataFrame(data)
    print(f"\nFlow Network Single Data:")
    print(f"  Rows: {len(df)}")
    print(f"  Columns: {df.columns.tolist()}")
    print(f"\nSample (first 10 rows):")
    print(df.head(10))
    
    return df

def generate_attribute_single_data():
    """
    Generate attribute network test data (single-subnet)
    Format: year source target source_value target_value
    
    Creates multiple attributes: GDP, unemployment, schooling
    """
    data = []
    
    # GDP data
    for year in years:
        for source in test_provinces:
            for target in test_provinces:
                if source != target:
                    # GDP values for source and target
                    source_gdp = np.random.uniform(10000, 50000)
                    target_gdp = np.random.uniform(10000, 50000)
                    
                    data.append({
                        'year': year,
                        'source': source,
                        'target': target,
                        'source_value': source_gdp,
                        'target_value': target_gdp
                    })
    
    df = pd.DataFrame(data)
    print(f"\nAttribute Network Single Data (GDP):")
    print(f"  Rows: {len(df)}")
    print(f"  Columns: {df.columns.tolist()}")
    print(f"\nSample (first 10 rows):")
    print(df.head(10))
    
    return df

def generate_attribute_multi_data():
    """
    Generate attribute network test data (multi-subnet)
    Format: year feature source target source_value target_value
    
    Example: GDP by sector
    """
    sectors = ['agriculture', 'manufacturing', 'services']
    data = []
    
    for year in years:
        for sector in sectors:
            for source in test_provinces:
                for target in test_provinces:
                    if source != target:
                        source_value = np.random.uniform(1000, 10000)
                        target_value = np.random.uniform(1000, 10000)
                        
                        data.append({
                            'year': year,
                            'feature': sector,
                            'source': source,
                            'target': target,
                            'source_value': source_value,
                            'target_value': target_value
                        })
    
    df = pd.DataFrame(data)
    print(f"\nAttribute Network Multi Data (GDP by sector):")
    print(f"  Rows: {len(df)}")
    print(f"  Columns: {df.columns.tolist()}")
    print(f"\nSample (first 10 rows):")
    print(df.head(10))
    
    return df

if __name__ == "__main__":
    print("="*60)
    print("GENERATING TEST DATASETS FOR NETWORKS ADO")
    print("="*60)
    
    # Generate all test datasets
    interaction_df = generate_interaction_data()
    flow_multi_df = generate_flow_multi_data()
    flow_single_df = generate_flow_single_data()
    attr_single_df = generate_attribute_single_data()
    attr_multi_df = generate_attribute_multi_data()
    
    # Save to CSV (will convert to Stata later)
    interaction_df.to_csv('/home/claude/networks-ado-project/examples/test_interaction_multi.csv', index=False)
    flow_multi_df.to_csv('/home/claude/networks-ado-project/examples/test_flow_multi.csv', index=False)
    flow_single_df.to_csv('/home/claude/networks-ado-project/examples/test_flow_single.csv', index=False)
    attr_single_df.to_csv('/home/claude/networks-ado-project/examples/test_attribute_single.csv', index=False)
    attr_multi_df.to_csv('/home/claude/networks-ado-project/examples/test_attribute_multi.csv', index=False)
    
    print("\n" + "="*60)
    print("TEST DATA SAVED TO examples/")
    print("="*60)
    print("\nFiles created:")
    print("  - test_interaction_multi.csv")
    print("  - test_flow_multi.csv")
    print("  - test_flow_single.csv")
    print("  - test_attribute_single.csv")
    print("  - test_attribute_multi.csv")
