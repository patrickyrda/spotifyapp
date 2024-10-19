//dynamic phrase 
const phrases = [
    "What music can't you stop listening to?",
    "Nice choice! What else would you like to add?",
    "You're on fire! Add another one.",
    "Keep adding the ones you like!"
];

let phraseIndex = 0;
const phraseElement = document.getElementById('phrase');

function changePhrase() {
    // First fade out the current phrase
    phraseElement.style.opacity = 0;

    // Wait for the fade-out effect to finish (500ms), then change the phrase and fade it in
    setTimeout(() => {
        if (phraseIndex + 1 < phrases.length) {
            phraseIndex += 1;
        }
        // Set the new phrase
        phraseElement.textContent = phrases[phraseIndex];

        // Fade in the new phrase
        phraseElement.style.opacity = 1;
    }, 500); // Wait for the fade-out transition (0.5s)
}


//function for search, display and manage adding of tracks in the bar
// Function to handle adding a track without reloading
function addToPlaylist(trackUri) {
    fetch(`/add/${encodeURIComponent(trackUri)}`, { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // Phrase changes only if adding the track is successful
                changePhrase();

                document.getElementById('search-input').value = '';
                document.getElementById('results').innerHTML = '';
            } else {
                alert(`Error: ${data.message}`);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

// Search and add tracks to playlist
document.getElementById('search-input').addEventListener('input', function() {
    const query = this.value;
    const resultsDiv = document.getElementById('results');

    // Clear results if the input is empty
    if (query.length === 0) {
        resultsDiv.innerHTML = '';
        resultsDiv.classList.remove('visible');
    } else {
        fetch(`/search?query=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                resultsDiv.innerHTML = ''; // Clear previous results
                
                // Show the results container with animation
                resultsDiv.classList.add('visible'); // Add class to trigger animation

                data.forEach(track => {
                    const trackElement = document.createElement('div');
                    trackElement.classList.add('result-item');
                    trackElement.innerHTML = `
                        <img src="${track.album_cover}" alt="Album cover">
                        ${track.name} by ${track.artist}
                    `;
                    resultsDiv.appendChild(trackElement);

                    // After adding the element to the DOM, trigger the slide-down effect
                    setTimeout(() => {
                        trackElement.classList.add('show');
                    }, 10); // Delay to allow for the class to apply

                    // Make the entire result item clickable
                    trackElement.addEventListener('click', function() {
                        addToPlaylist(track.uri); // Add the track to the playlist when the result item is clicked
                    });
                });
            });
    }
});
