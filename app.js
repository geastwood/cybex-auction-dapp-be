var app = require('express')()
var server = require('http').Server(app)
var io = require('socket.io')(server)

server.listen(8080)
console.log('socket started on port:', 8080)

//// no need for index.html
// app.get('/', function(req, res) {
//   res.sendFile(__dirname + '/index.html')
// })

io.on('connection', function(socket) {
  // setInterval(() => {
  //   socket.emit('data', { hello: 'world' })
  // }, 30000)

  socket.on('message', function(data) {
    console.log('received on server:', data)
    socket.broadcast.emit('data', data)
  })
})
