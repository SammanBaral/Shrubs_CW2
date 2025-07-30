let thumbnails = document.querySelectorAll('.thumbnail .item');
let subMenu = document.getElementById("subMenu")

thumbnails.forEach((thumbnail, index) => {
    thumbnail.addEventListener('click', () => {
        itemActive = index;
        showSlider();
    })
})
const toggleMenu=()=>{
    subMenu.classList.toggle("open-menu")
}

function showTab(tabId) {
    // Hide all tab contents 
    var tabContents = document.querySelectorAll('.content_body');
    tabContents.forEach(function (content) {
        content.classList.remove('active');
    });

    // Show the selected tab content
    var selectedTab = document.getElementById(tabId);
    if (selectedTab) {
        selectedTab.classList.add('active');
    }
}