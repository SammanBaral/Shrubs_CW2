$(document).ready(function() {
    // Initial setup: set the main_image class for the first image
    $('.other_image:first-child a').addClass('selected');

    // Handle image click event
    $('.clickable-image').click(function(e) {
        e.preventDefault(); // Prevent the default behavior of the anchor tag

        // Remove 'selected' class from all anchor tags
        $('.clickable-image').removeClass('selected');

        // Set 'selected' class for the clicked anchor tag
        $(this).addClass('selected');

        // Get the URL of the clicked image from the data attribute
        var newMainImageSrc = $(this).data('main-image');

        // Set the main_image source to the clicked image
        $('.main_image img').attr('src', newMainImageSrc);
    });
});
