// app.js
document.addEventListener('DOMContentLoaded', () => {
    const fetchData = (name = '') => {
      const url = new URL('http://localhost:5000/api/data');//local host 5000
      if (name) {
        url.searchParams.append('name', name);
      }
  
      fetch(url)
        .then(response => response.json())
        .then(data => {
          const dataContainer = document.getElementById('data-container');
          dataContainer.innerHTML = ''; // Clear previous data
          data.forEach(item => {
            const div = document.createElement('div');
            div.textContent = `ID: ${item.id}, Name: ${item.name}`;
            dataContainer.appendChild(div);
          });
        })
        .catch(error => console.error('Error fetching data:', error));
    };
  
    const addData = (name) => {
      fetch('http://localhost:5000/api/data', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ name })
      })
      .then(response => response.json())
      .then(data => {
        console.log('Data added:', data);
        fetchData(); // Refresh the data display
      })
      .catch(error => console.error('Error adding data:', error));
    };
  
    // Fetch data when the fetch button is clicked
    document.getElementById('fetch-button').addEventListener('click', () => {
      const nameInput = document.getElementById('name-input').value;
      fetchData(nameInput);
    });
  
    // Add data when the add button is clicked
    document.getElementById('add-button').addEventListener('click', () => {
      const newNameInput = document.getElementById('new-name-input').value;
      addData(newNameInput);
    });
  
    // Fetch all data on initial load
    fetchData();
  });
  
