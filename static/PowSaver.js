function viewcheck(){
    let viewport = document.visibilityState
    if (viewport === "visible"){
        console.log("Active!")
        document.body.classList.remove("inactive")
    } else {
        console.log("Not in use, unactivating")
        document.body.classList.add("inactive")
    }
}

viewcheck();
document.addEventListener("visibilitychange", viewcheck);
