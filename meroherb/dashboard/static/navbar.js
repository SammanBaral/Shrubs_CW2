let thumbnails = document.querySelectorAll('.thumbnail .item');
let subMenu = document.getElementById("subMenu")


// click thumbnail

thumbnails.forEach((thumbnail, index) => {
    thumbnail.addEventListener('click', () => {
        itemActive = index;
        showSlider();
    })
})
const toggleMenu=()=>{
    subMenu.classList.toggle("open-menu")
}