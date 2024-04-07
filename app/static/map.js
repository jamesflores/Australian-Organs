window.initMap = function() {
    var map = new google.maps.Map(document.getElementById('map'), {
        zoom: 10,
        center: {lat: -33.8688, lng: 151.2093}  // Sydney
    });

    // Try to get the user's location
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function(position) {
            var userLocation = {
                lat: position.coords.latitude,
                lng: position.coords.longitude
            };

            // Reverse geocode the user's location to get the country
            var geocoder = new google.maps.Geocoder;
            geocoder.geocode({'location': userLocation}, function(results, status) {
                if (status === 'OK') {
                    if (results[0]) {
                        // Find the country among the address components
                        var country = results[0].address_components.find(function(component) {
                            return component.types.includes('country');
                        });

                        // If the country is Australia, set the map's center to the user's location
                        // Otherwise, keep the map's center at Sydney
                        if (country && country.long_name === 'Australia') {
                            map.setCenter(userLocation);
                        }
                    }
                }

                // Call updateMarkers after the map's center has been set
                updateMarkers();
            });
        }, function() {
            // If the user denies the Geolocation request or it fails for some other reason, do nothing
            // The map will just stay centered on the default location
            updateMarkers();
        });
    } else {
        // If Geolocation is not supported by the user's browser, call updateMarkers with the default location
        updateMarkers();
    }

    function updateMarkers() {
        var center = map.getCenter();
        var lat = center.lat();
        var lon = center.lng();
        var radius = 50;  // km

        var currentInfoWindow = null;  // Keep track of the currently open info window
        $.ajax({
            url: "https://api.ohta.org.au/geosearch/",
            data: {'lat': lat, 'lon': lon, 'radius': radius},
            dataType: 'json',
            success: function(data) {
                data.forEach(function(organ) {
                    var marker = new google.maps.Marker({
                        position: {lat: organ.latitude, lng: organ.longitude},
                        map: map,
                        title: organ.name,
                        clicked: false
                    });

                    var infoWindow = new google.maps.InfoWindow({
                        content: `
                            <div class="row">
                                <div class="col-md-4">
                                    <a href="${organ.url}" target="_blank">
                                        <img src="${organ.image}" alt="${organ.name}" style="max-width:100%; max-height:100%;" loading="lazy">
                                    </a>
                                </div>
                                <div class="col-md-8">
                                    <a href="${organ.url}" target="_blank">
                                        <h5>${organ.name}</h5>
                                    </a>
                                    <p>${organ.address}, ${organ.city}, ${organ.state} ${organ.postcode}</p>
                                    <p>${organ.description}</p>
                                </div>
                            </div>
                        `
                    });

                    var clicked = false;

                    marker.addListener('mouseover', function() {
                        // Close the current info window if it's open
                        if (currentInfoWindow) {
                            currentInfoWindow.close();
                        }
                        
                        // Open the info window for the current marker
                        this.clicked = true;
                        infoWindow.open(map, marker);

                        // Set the current info window to the one that was just opened
                        currentInfoWindow = infoWindow;
                    });
                    marker.addListener('mouseout', function() {
                        if (!clicked)
                            infoWindow.close();
                    });
                    marker.addListener('click', function() {
                        clicked = true;
                        infoWindow.open(map, marker); 
                    });
                });
            }
        });
    }

    map.addListener('dragend', function() {
        updateMarkers();
    });
    updateMarkers();
}

window.onload = initMap;