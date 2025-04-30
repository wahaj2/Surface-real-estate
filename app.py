import streamlit as st
import pandas as pd
import os

# Load data with better state management
def load_data():
    try:
        if not os.path.exists('data.csv'):
            return pd.DataFrame(columns=['Plot no', 'Block', 'Property office', 'Demand (lacs)', 'contact number'])
        
        data = pd.read_csv('data.csv')
        data['Plot no'] = data['Plot no'].astype(str)
        
        # Handle contact number column
        contact_cols = [col for col in data.columns if 'contact' in col.lower()]
        if contact_cols:
            data['contact number'] = data[contact_cols[0]].astype(str).replace('nan', '')
            if len(contact_cols) > 1:
                data = data.drop(columns=contact_cols[1:])
        else:
            data['contact number'] = ''
        
        return data
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame(columns=['Plot no', 'Block', 'Property office', 'Demand (lacs)', 'contact number'])

def save_data(data):
    try:
        data.to_csv('data.csv', index=False)
    except Exception as e:
        st.error(f"Error saving data: {e}")

def main():
    st.title('Property Data Management Dashboard')
    
    # Initialize session state for data if it doesn't exist
    if 'property_data' not in st.session_state:
        st.session_state.property_data = load_data()
    
    # Sidebar for operations
    st.sidebar.header("Data Operations")
    
    # Add new record form
    with st.sidebar.form("add_form"):
        st.subheader("Add New Record")
        new_plot = st.text_input("Plot no")
        new_block = st.text_input("Block").upper()
        new_office = st.text_input("Property office")
        new_demand = st.number_input("Demand (lacs)", min_value=0)
        new_contact = st.text_input("Contact number (11 digits)", max_chars=11)
        
        submitted = st.form_submit_button("Add Record")
        if submitted:
            if new_plot and new_block and new_office:
                new_record = pd.DataFrame([{
                    'Plot no': str(new_plot),
                    'Block': new_block,
                    'Property office': new_office,
                    'Demand (lacs)': new_demand,
                    'contact number': new_contact
                }])
                # Update both session state and CSV file
                st.session_state.property_data = pd.concat([st.session_state.property_data, new_record], ignore_index=True)
                save_data(st.session_state.property_data)
                st.sidebar.success("Record added successfully!")
                st.rerun()
            else:
                st.sidebar.error("Please fill in all required fields (Plot no, Block, Property office)")
    
    # Delete record
    with st.sidebar.form("delete_form"):
        st.subheader("Delete Record")
        plot_to_delete = st.text_input("Plot no to delete")
        block_to_delete = st.text_input("Block of record to delete").upper()
        
        submitted_delete = st.form_submit_button("Delete Record")
        if submitted_delete:
            if plot_to_delete and block_to_delete:
                initial_count = len(st.session_state.property_data)
                # Update the session state data
                st.session_state.property_data = st.session_state.property_data[
                    ~((st.session_state.property_data['Plot no'] == str(plot_to_delete)) & 
                      (st.session_state.property_data['Block'] == block_to_delete))
                ]
                if len(st.session_state.property_data) < initial_count:
                    save_data(st.session_state.property_data)
                    st.sidebar.success("Record deleted successfully!")
                    st.rerun()
                else:
                    st.sidebar.error("No matching record found to delete")
            else:
                st.sidebar.error("Please provide both Plot no and Block")
    
    # Main display area
    st.header("Property Data")
    
    # Check if we have data to display
    if st.session_state.property_data.empty:
        st.warning("No data available. Please add records using the sidebar form.")
    else:
        # Get unique blocks for filter
        unique_blocks = sorted(st.session_state.property_data['Block'].unique().tolist())
        
        # Add a new block option to the filter
        new_block_filter = st.text_input("Add new Block to filter").upper()
        if new_block_filter and new_block_filter not in unique_blocks:
            unique_blocks.append(new_block_filter)
        
        # Block filter dropdown
        selected_block = st.selectbox("Filter by Block", ['All'] + unique_blocks)
        
        # Filter data based on selection
        if selected_block != 'All':
            filtered_data = st.session_state.property_data[st.session_state.property_data['Block'] == selected_block]
        else:
            filtered_data = st.session_state.property_data.copy()
        
        # Display the filtered data
        st.dataframe(filtered_data, hide_index=True, use_container_width=True)
        
        # Show statistics
        st.subheader("Statistics")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Properties", len(filtered_data))
        with col2:
            avg = filtered_data['Demand (lacs)'].mean()
            st.metric("Average Demand", f"{avg:.1f} lacs" if not pd.isna(avg) else "N/A")
        with col3:
            total = filtered_data['Demand (lacs)'].sum()
            st.metric("Total Demand", f"{total:.1f} lacs" if not pd.isna(total) else "N/A")
        
        # Group by Property office
        st.write("Demand by Property Office")
        office_stats = filtered_data.groupby('Property office')['Demand (lacs)'].agg(['count', 'sum', 'mean'])
        st.dataframe(office_stats.style.format({'sum': '{:.1f}', 'mean': '{:.1f}'}))

if __name__ == '__main__':
    main()