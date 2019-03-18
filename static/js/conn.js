////////////////////////////////////////////////////////////////////
clients = {}
function createconn(connectedcallback){
    //console.log("creating socket", SOCKET_SUBMIT_URL)
    rawsocket = io.connect(SOCKET_SUBMIT_URL)
    //console.log("socket created")

    function onconnect(){
        //console.log("socket connected")
        connectedcallback()
    }

    function siores(resobj){
        //console.log("siores", resobj)
        clients[resobj.id].siores(resobj)
    }

    rawsocket.on("connect", onconnect)
    rawsocket.on("siores", siores)
}
////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////
// connwidget
class CButton_ extends Button_{
        constructor(caption, action){
            super(caption, action)
            this.fs(20).bdw(0).bc("inherit").c("#009").pad(0)
        }
}
function CButton(caption, action){return new CButton_(caption, action)}

class ConnWidget_ extends e{
    constructor(id){
        super("div")
        this.id = id
        clients[this.id] = this
    }

    sioreq(reqobj){
	//console.log(reqobj)
        reqobj.id = this.id
        rawsocket.emit("sioreq", reqobj)
    }

    siores(resobj){
        //console.log("default siores handler", this.id, resobj)
    }
}
////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////
// board
function stripsan(san){
    if(san.includes("..")){
        let parts = san.split("..")
        return parts[1]
    }
    if(san.includes(".")){
        let parts = san.split(".")
        return parts[1]
    }
    return san
}

class GameNode_ extends e{
	constructor(){
		super("div")
		this.disp("flex").ai("center").fd("row").ac("unselectable").mar(1)
		this.parboard = null
		this.par = null
		this.san = null
		this.childs = {}
		this.movediv = Div().bc("#eee").mw(70).w(60).mh(20).h(20).disp("flex").ai("center").jc("space-around").cp()
		this.childsdiv = Div().disp("flex").ai("left").jc("space-around").fd("column").bc("#eee")		
		this.a(this.movediv, this.childsdiv)
	}
	line(){
		let current = this
		let movelist = []
		while(current.par){
			movelist.unshift(stripsan(current.san))
			current = current.par
		}
		return movelist
	}
	build(){
		let captiondiv = Div().html(this.san ? this.san : "root")
		this.movediv.x.a(captiondiv).bds("solid").bdw(1).bdc("#777")
		this.movediv.ae("mousedown", this.parboard.gamenodeclicked.bind(this.parboard, this.line()))
        this.childsdiv.x
        if((Object.keys(this.childs).length > 1)||(!this.par)){
            this.childsrgb = randrgb()        
            this.mult = 1    
        }else{
            this.childsrgb = this.par.childsrgb                        
            this.mult = this.par.mult + 1
            if(this.mult > 3) this.mar(0)
        }
        this.childsdiv.bc(this.childsrgb)
		for(let childsan in this.childs){
			this.childsdiv.a(this.childs[childsan].build())
		}
		return this
	}
	highlight(line){
		this.movediv.bc("#afa").bdc("#000")
		if(!line) return
		if(line.length > 0){
			let san = line.shift()
			this.childs[san].highlight(line)
		}else{
			this.movediv.scrollIntoView({
				block: "center",
				inline: "center"
			})
		}
	}
	fromobj(parboard, obj, par, gensan){
		this.parboard = parboard
		this.childs = {}
		this.par = par
		this.san = gensan
		for(let childsan in obj){
			let childobj = obj[childsan]
			this.childs[childsan] = GameNode().fromobj(this.parboard, childobj, this, childsan)
		}
		return this
	}
}
function GameNode(){return new GameNode_()}

class Board_ extends ConnWidget_{
	gamenodeclicked(line){
		//console.log(line)
		
		this.sioreq({
			kind: "setline",
			line: line
		})
	}
    del(){
        this.sioreq({
            kind: "delmove"            
        })
    }

    tobegin(){
        this.sioreq({
            kind: "tobegin"            
        })
    }

    back(){
        this.sioreq({
            kind: "backmove"            
        })
    }

    forward(){
        this.sioreq({
            kind: "forwardmove"            
        })
    }

    toend(){
        this.sioreq({
            kind: "toend"            
        })
    }

    reset(ev, pgn, fen){                
        this.sioreq({
            kind: "getboard",
            newgame: true,
            variantkey: this.basicboard.variantkey,
            pgn: pgn,
            fen: fen
        })
    }

    totalheight(){
        return this.basicboard.totalheight + this.controlheight
    }

    pgnpath(){
        return this.id + "/variants/" + this.basicboard.variantkey + "/pgn"
    }

    flippath(){
        return this.id + "/variants/" + this.basicboard.variantkey + "/flip"
    }

    setpgn(pgn){        
        this.pgn = pgn || localStorage.getItem(this.pgnpath())        
        if(this.pgn) localStorage.setItem(this.pgnpath(), this.pgn)
        else localStorage.removeItem(this.pgnpath())
        if(this.pgndiv) this.pgntext.setText(this.pgn || "loading game ...")        
    }

    setvariantkey(variantkey){        
        this.args.variantkey = variantkey
        this.basicboard = BasicBoard(this.args)        
        this.resize(this.resizewidth, this.resizeheight)        
        localStorage.setItem(this.id + "/variantkey", this.basicboard.variantkey)                
    }

    variantcombochanged(){                
        let variantkey = this.variantcombo.v()        
        this.setvariantkey(variantkey)
        this.setpgn(null)
        this.reset(null, this.pgn, null)
    }

    fenpastecallback(fen){
        this.reset(null, null, fen)
    }

    pgnpastecallback(pgn){        
        this.reset(null, pgn, null)
    }

    buildvariantcombo(){        
        this.variantcombo = Select().setoptions(VARIANT_KEYS, this.basicboard.variantkey)
        this.variantcombo.ae("change", this.variantcombochanged.bind(this)).fs(14).pad(2)
        this.variantcombohook.x.a(this.variantcombo)
    }

	buildtree(){
		//this.treediv.x.html("<pre>" + JSON.stringify(this.tree, null, 2) + "</pre>")
		this.rootgamenode = GameNode().fromobj(this, this.tree, null, null)
		setseed(1)
		this.treediv.x.a(this.rootgamenode.build())
		this.rootgamenode.highlight(this.line)
    }
    
    analyzelichess(){
        let url = `https://lichess.org/analysis/${this.basicboard.variantkey}/${this.basicboard.fen}`
        window.open(url, "_blank")
    }

    mergepgnpastecallback(pgn){
        this.sioreq({
            "kind": "mergepgn",
            "pgn": pgn
        })
    }

    getflip(){
        return localStorage.getItem(this.flippath()) ? true : false
    }

    setflip(flip){
        if(flip) localStorage.setItem(this.flippath(), "true")
        else localStorage.removeItem(this.flippath())
        this.basicboard.setflip(flip)
    }

    flip(){
        this.setflip(!this.getflip())        
        this.basicboard.buildall()
    }

    build(){        
        this.boardwidth = this.basicboard.totalwidth()
        this.maincontainer = Div().disp("flex").fd("column")
        this.controlpanel = Div().disp("flex").ai("center").jc("space-around").bc("#eef").h(this.controlheight - this.fenheight).w(this.boardwidth)
        this.variantcombohook = Div()
        this.controlpanel.a(this.variantcombohook)
        this.buildvariantcombo()        
        this.controlpanel.a(CButton("✖", this.del.bind(this)).c("#a00"))
        this.controlpanel.a(CButton("⏮", this.tobegin.bind(this)).mb(3))
        this.controlpanel.a(CButton("◀", this.back.bind(this)).c("#0a0"))
        this.controlpanel.a(CButton("▶", this.forward.bind(this)).c("#0a0"))
        this.controlpanel.a(CButton("⏭", this.toend.bind(this)).mb(3))
        this.controlpanel.a(CButton("↩", this.reset.bind(this)).fs(35).c("#f00").mt(8))
        this.controlpanel.a(CButton("↕", this.flip.bind(this)).fs(25))        
        this.controlpanel.a(Button("Analyze lichess", this.analyzelichess.bind(this)))        
        this.fentext = CopyText({width:this.boardwidth, height:this.fenheight, pastecallback:this.fenpastecallback.bind(this)})
        this.maincontainer.a(this.controlpanel, this.fentext, this.basicboard)
        this.guicontainer = Div().disp("flex")                              
        this.pgndiv = Div()
        this.mergepgndiv = Div()
	    this.treediv = Div().ff("monospace").pad(5)
        this.guitabpane = TabPane(this.id + "/guitabpane", {width:this.guiwidth, height:this.totalheight()}).settabs([
            Tab("pgn", "PGN", this.pgndiv),   
            Tab("mergepgn", "Merge PGN", this.mergepgndiv),         
            Tab("tree", "Tree", this.treediv),            
            Tab("book", "Book", this.bookdiv = Div())
        ]).selecttab("pgn", USE_STORED_IF_AVAILABLE)        
        this.pgntext = CopyTextArea({
            width:this.guiwidth - getScrollBarWidth(),
            height:this.guitabpane.contentheight - getScrollBarWidth(),
            pastecallback: this.pgnpastecallback.bind(this)
        })
        this.pgndiv.a(this.pgntext)
        this.mergepgntext = CopyTextArea({
            width:this.guiwidth - getScrollBarWidth(),
            height:this.guitabpane.contentheight - getScrollBarWidth(),
            pastecallback: this.mergepgnpastecallback.bind(this)
        })
        this.mergepgndiv.a(this.mergepgntext)
        this.setpgn()
	    this.buildtree()
        this.guicontainer.a(this.maincontainer, this.guitabpane)
        this.x.a(this.guicontainer)
        return this
    }

    resize(width, height){        
        this.resizewidth = width
        this.resizeheight = height
        this.basicboard.flip = this.getflip()
        this.basicboard.resize(width, height - this.controlheight)
        this.guiwidth = width - this.basicboard.totalwidth()
        this.build()
    }

    dragmovecallback(m){
        let algeb = m.toalgeb()        
        this.sioreq({
            "kind": "makealgebmove",
            "algeb": m.toalgeb()
        })
    }

    constructor(id, args){
        super(id)
        this.args = args
        this.boardheight = args.boardheight || 300
        this.fenheight = 20 || args.fenheight
        this.controlheight = 60 || args.controlheight
        this.guiwidth = args.guiwidth || 400
        this.args.dragmovecallback = this.dragmovecallback.bind(this)
        this.args.variantkey = localStorage.getItem(this.id + "/variantkey") || "standard"
        this.basicboard = BasicBoard(this.args)    
	    this.tree = {}
        //localStorage.removeItem(this.pgnpath())    
        this.setpgn()        
        this.build()

	this.tree = {}
        this.sioreq({
            kind: "getboard",
            newgame: true,
            variantkey: this.basicboard.variantkey,
            pgn: this.pgn
        })
    }

    siores(obj){        
        if(obj.kind == "setboard"){            
            let variantkey = obj.variantkey
            this.setvariantkey(variantkey)
            let fen = obj.fen
            let pgn = obj.pgn
            this.basicboard.setfromfen(fen)            
            this.setpgn(pgn)
            this.fentext.setText(fen)
		this.tree = obj.tree
		this.line = obj.line
		this.buildtree()
        }
    }
}
function Board(id, args){return new Board_(id, args)}
////////////////////////////////////////////////////////////////////
