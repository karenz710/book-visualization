document.getElementById('searchForm').addEventListener('submit', async function (e) {
    e.preventDefault();

    const title = document.getElementById('bookTitle').value;
    console.log('Searching for book:', title);

    // Step 1: Search for the book and add it to the database
    await fetch(`http://127.0.0.1:5000/search?title=${encodeURIComponent(title)}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Error adding book');
            }
            return response.json();
        })
        .then(data => {
            console.log('Book added:', data);
        })
        .catch(error => {
            console.error('Error:', error);
        });

    // Step 2: Fetch and display the entire visualization data
    updateGraph();
});

function clearGraph() {
    const chartElement = document.getElementById('bookChart');
    Plotly.purge(chartElement);

    // Call the backend to clear the database
    fetch('http://127.0.0.1:5000/clear', {
        method: 'POST'
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Error clearing database');
            }
            return response.json();
        })
        .then(data => {
            console.log(data.message);
        })
        .catch(error => console.error('Error clearing database:', error));
}

function updateGraph() {
    // Fetch the visualization data
    fetch('http://127.0.0.1:5000/visualize')
        .then(response => {
            if (!response.ok) {
                throw new Error('Error fetching visualization data');
            }
            return response.json();
        })
        .then(data => {
            console.log('Visualization data:', data);
            if (data.length > 0) {
                // Prepare data for scatter plot
                const xValues = data.map(book => book.publication_date);
                const yValues = data.map(book => book.publication_place || 'Unknown');
                const textValues = data.map(book => book.title);

                // Prepare annotations
                const annotations = data.map(book => ({
                    x: book.publication_date,
                    y: book.publication_place || 'Unknown',
                    text: ``,
                    xanchor: 'center',
                    yanchor: 'bottom',
                    showarrow: false
                }));

                // Display the data on the scatter plot
                const plotData = [{
                    x: xValues,
                    y: yValues,
                    mode: 'markers+text',
                    type: 'scatter',
                    text: textValues,
                    textposition: 'top center',
                    marker: { size: 12 },
                    name: 'Books'
                }];

                const layout = {
                    title: 'Books Visualization: Publication Date and Publication Place',
                    xaxis: {
                        title: 'Publication Date',
                        type: 'linear'
                    },
                    yaxis: {
                        title: '',
                        type: 'category',
                        categoryorder: 'array',
                        categoryarray: Array.from(new Set(yValues))
                    },
                    annotations: annotations,
                    height: 600,  // Increase height of the plot
                    margin: {
                        l: 100,  // Increase left margin to allow more space for Y-axis labels
                        r: 50,
                        t: 50,
                        b: 100  // Increase bottom margin to avoid cutting off X-axis labels
                    }
                };

                Plotly.newPlot('bookChart', plotData, layout);
            } else {
                console.error('No data available to visualize');
            }
        })
        .catch(error => console.error('Error fetching visualization data:', error));
}
