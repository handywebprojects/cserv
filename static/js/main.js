////////////////////////////////////////////////////////////////////
class MainConnWidget extends ConnWidget_{
    constructor(){
        super("main")        
    }

    siores(resobj){
        //console.log("main received", resobj)
        if(resobj.kind == "connectedack"){
            buildapp()
        }
    }
}
mcw = new MainConnWidget()
createconn(function(){
    mcw.sioreq({
        kind: "connected"        
    })
})
////////////////////////////////////////////////////////////////////
board = Board("mainboard", {})

function usercallback(){
    console.log("main user changed")
    board.sioreq({
        "kind": "getgame"
    })
}

function buildapp(){
    let maintabpane = TabPane("maintabpane", {fillwindow:true}).settabs([        
        Tab("board", "Board", board),  
        ProfileTab({usercallback: usercallback}),
        Tab("about", "About", Div().pad(5).html("Chess server."))    
    ]).selecttab("board", USE_STORED_IF_AVAILABLE)

    se("root", maintabpane)
}
////////////////////////////////////////////////////////////////////
