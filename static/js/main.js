////////////////////////////////////////////////////////////////////
class MainConnWidget extends ConnWidget_{
    constructor(){
        super("main")        
    }

    siores(resobj){
        //console.log("main received", resobj)
        if(resobj.kind == "connectedack"){
            buildapp(resobj)
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

function buildapp(resobj){
    try{
        readmehtml = markdownconverter.makeHtml(resobj.readme_md)
        console.log(readmehtml)
    }catch(err){
        console.log(err)
        readme = "Chess Server."
    }

    let maintabpane = TabPane("maintabpane", {fillwindow:true, bimg: "static/img/backgrounds/marble.jpg"}).settabs([        
        Tab("board", "Board", board),  
        ProfileTab({usercallback: usercallback}),
        Tab("about", "About", Div().pl(15).html(readmehtml))    
    ]).selecttab("board", USE_STORED_IF_AVAILABLE)

    se("root", maintabpane)
}
////////////////////////////////////////////////////////////////////
