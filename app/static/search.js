var nextPageUrl = null;

function clearResults() {
    $("#results").html('');
    nextPageUrl = null;
}

function performSearch(url) {
    console.log("Search:", url);
    $("#loading").show();
    $("#search").prop('disabled', true);

    $.ajax({
        url: url,
        method: "GET",
        success: function(response) {
            console.log("Response:", response);
            $("#loading").hide();
            
            response.results.forEach(function(item) {
                var card = $('<div class="card mb-3"></div>');
                var cardRow = $('<div class="row g-0"></div>');  // Bootstrap grid row
                
                var cardImgCol = $('<div class="col-md-4"></div>');  // Column for the image
                var imgHtml = item.main_image ? '<img src="' + item.main_image + '" class="img-fluid rounded-start" alt="' + item.name +'">' : '<div class="img-fluid rounded-start" style="background: #f0f0f0; height: 150px;"></div>';
                cardImgCol.append(imgHtml);

                var cardBodyCol = $('<div class="col-md-8"></div>');  // Column for the text
                var cardBody = $('<div class="card-body"></div>');
                var cardContent = '';
                
                cardContent += '<h5 class="card-title"><a href="' + item.url + '" target="_blank">' + item.name + '</a></h5>';
                cardContent += '<p class="card-text"><small class="text-muted">' + item.builder + '</small></p>';
                cardContent += '<p class="card-text">' + item.address + ', ' + item.city + ' ' + item.state + ', ' + item.postcode + '</p>';
                cardContent += '<p class="card-text">' + item.description + '</p>';
                
                cardBody.append(cardContent);
                cardBodyCol.append(cardBody);
                
                cardRow.append(cardImgCol).append(cardBodyCol);
                card.append(cardRow);
                $("#results").append(card);
            });

            nextPageUrl = response.next;
            $("#search").prop('disabled', false);
        },
        error: function(error) {
            console.error("Error:", error);
            $("#results").html('<div class="mt-3">No results found.</div>');
            $("#loading").hide();
            $("#search").prop('disabled', false);
        }
    });
}

$(document).ready(function() {
    var url = "https://api.australianorgans.com.au";

    $("#search").click(function() {
        clearResults();
        var query = $("#q").val();
        performSearch(`${url}/search/?q=${query}`);
    });

    $("#q").keydown(function(event) {
        if (event.key === 'Enter' && !$("#search").prop('disabled')) {
            clearResults();
            $("#search").click();
        }
    });

    $(window).scroll(function() {
        var scrollPosition = $(window).scrollTop() + $(window).height();
        var nearBottom = $(document).height() - 10;

        if (scrollPosition >= nearBottom) {
            if (nextPageUrl && !$("#search").prop('disabled')) {
                console.log("Loading more results...");
                performSearch(nextPageUrl);
            }
        }
    });

    performSearch(`${url}/organs/?random_order=true`)  // Load random organs on page load
});