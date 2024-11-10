window.initMap = function() {
    var map = new google.maps.Map(document.getElementById('map'), {
        zoom: 10,
        center: {lat: -33.8688, lng: 151.2093}  // Sydney: default
    });

    getUserLocation(map);  // Attempt to center the map on the user's location if available
    loadAllMarkers(map);   // Load all markers at once

    // Set up search box functionality
    var input = document.getElementById('search-box');
    input.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            return false;
        }
    });
    var searchBox = new google.maps.places.SearchBox(input);
    searchBox.addListener('places_changed', function() {
        var places = searchBox.getPlaces();
        if (places.length == 0) {
            return;
        }

        places.forEach(function(place) {
            if (!place.geometry) {
                console.log("Returned place contains no geometry");
                return;
            }
            map.setCenter(place.geometry.location);
        });

        map.setZoom(14);
    });
};

function loadAllMarkers(map) {
    var currentInfoWindow = null;
    var page = 1;
    var pageSize = 50;

    function fetchMarkers() {
        $.ajax({
            url: `https://api.australianorgans.com.au/organs/?page=${page}&page_size=${pageSize}`,
            dataType: 'json',
            success: function(response) {
                response.results.forEach(function(organ) {
                    var marker = new google.maps.Marker({
                        position: {lat: organ.latitude, lng: organ.longitude},
                        map: map,
                        title: organ.name
                    });

                    var location = '';
                    if (organ.address) location = `${organ.address}, `;
                    if (organ.city) location += `${organ.city}, `;
                    if (organ.state) location += `${organ.state} `;
                    if (organ.postcode) location += `${organ.postcode}`;

                    var infoWindow = new google.maps.InfoWindow({
                        content: `
                            <div class="row">
                                ${organ.main_image ? `
                                <div class="col-md-4">
                                    <a href="https://australianorgans.com.au/r/?url=${organ.url}" target="_blank">
                                        <img src="${organ.main_image}" alt="${organ.name}" style="max-width:100%; max-height:100%;" loading="lazy">
                                    </a>
                                </div>` : ''}
                                <div class="${organ.main_image ? 'col-md-8' : 'col-md-12'}">
                                    <a href="https://australianorgans.com.au/r/?url=${organ.url}" target="_blank">
                                        <h5>${organ.name}</h5>
                                    </a>
                                    <p>${location}</p>
                                    <p>${organ.description}</p>
                                </div>
                            </div>
                        `
                    });

                    marker.addListener('mouseover', function() {
                        if (currentInfoWindow) {
                            currentInfoWindow.close();
                        }
                        infoWindow.open(map, marker);
                        currentInfoWindow = infoWindow;
                    });

                    marker.addListener('mouseout', function() {
                        infoWindow.close();
                    });

                    marker.addListener('click', function() {
                        infoWindow.open(map, marker); 
                    });
                });

                // If there's a next page, increment the page number and fetch the next page
                if (response.next) {
                    page += 1;
                    fetchMarkers();
                }
            },
            error: function() {
                console.error("Failed to load markers from API");
            }
        });
    }

    fetchMarkers();  // Start fetching markers
}

function getUserLocation(map) {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function(position) {
            var userLocation = {
                lat: position.coords.latitude,
                lng: position.coords.longitude
            };

            map.setCenter(userLocation);  // Center the map on user's location
            map.setZoom(10);               // Zoom in on the user's area
        }, function() {
            console.log("Geolocation request denied or failed.");
        });
    }
}

window.onload = initMap;