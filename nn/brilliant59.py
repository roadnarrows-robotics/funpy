# The brilliant.org 2020 100-day challenge.
# Day 59

from itertools import product

class Neuron:
  def __init__(self, weights, bias=0):
    self.weights = weights
    self.bias = bias
    self.astate = 0

  def activate(self, inputs):
    self.astate = \
        1 if sum([i*w for i,w in zip(inputs, self.weights)]) >= self.bias else 0
    return self.astate

  def activation_state(self):
    return self.astate

class Layer:
  def __init__(self, neurons):
    self.neurons = neurons

  def feedforward(self, inputs):
    astate = []
    for neuron in self.neurons:
      astate.append(neuron.activate(inputs))
    return astate

  def activation_state(self):
    return [n.activation_state() for n in self.neurons] 

class NeuralNetwork:
  def __init__(self, layers):
    self.layers = layers

  def run(self, inputs):
    for layer in self.layers:
      inputs = layer.feedforward(inputs)
    return inputs

  def activation_state(self):
    return [l.activation_state() for l in self.layers] 

if __name__ == '__main__':
  bias = 2
  nn = NeuralNetwork([
        Layer([
          Neuron([-1, -1, 1, 1, 1], bias),
          Neuron([1, -1, -1, 1, 1], bias),
          Neuron([1, 1, -1, -1, 1], bias),
          Neuron([1, 1, 1, 1, -1], bias),
        ]),
        Layer([
          Neuron([1, 1, 1, 1], bias),
          Neuron([1, 1, 1, -1], bias),
          Neuron([1, 1, -1, 1], bias),
        ]),
        Layer([
          Neuron([1, -1, 1], bias),
          Neuron([1, 1, 1], bias),
        ]),
        Layer([
          Neuron([1, 1], bias),
        ]),
      ])
  
  input_dataset = product((0,1), repeat=5)

  for inputs in input_dataset:
    output = nn.run(inputs)
    if output[0] == 1:
      print(inputs)
      for astate in nn.activation_state():
        print(astate)
      print()
